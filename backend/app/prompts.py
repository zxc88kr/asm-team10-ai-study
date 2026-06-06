"""시스템 프롬프트 + 구조화 출력 스키마 (구현스펙 §5, §6 / 오케스트레이션 §2).

환각 방지의 핵심: reason/evidence 를 필수 필드로 두어 '근거 없는 카드/판정'을 구조로 차단한다.
"""

# --- 의도 분류 (solar-mini) ---
# 주의: langchain의 with_structured_output(dict)은 top-level "title"을 함수명으로 요구한다.
INTENT_SCHEMA = {
    "title": "classify_intent",
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "chitchat", "provide_info", "edit_condition",
                "ask_listing", "select_listing", "ask_location",
            ],
        },
        "edit": {
            "type": "object",
            "properties": {
                "field": {"type": "string", "enum": ["rent", "deposit", "commute_max", "area", "mgmt_fee_max"]},
                "op": {"type": "string", "enum": ["set", "inc", "dec"]},
                "value": {"type": "number"},
            },
        },
    },
    "required": ["intent"],
}

INTENT_SYSTEM = """사용자의 마지막 발화 의도를 분류한다.
- provide_info: 생활/조건 정보를 새로 말함 (니즈 단계 일반 입력)
- edit_condition: 기존 조건(예산/월세/보증금)을 바꿈. 예 "월세 5만 더"→{field:rent,op:inc,value:5}, "예산 60으로"→{field:rent,op:set,value:60}
- ask_listing: 추천된 특정 매물에 대한 질문. 예 "C는 방음 어때요?"
- ask_location: 입지/통학/밤길/막차/거리/위치 설명 요청. 예 "입지 설명해줘", "통학 얼마나 걸려?", "밤길 안전해?"
- select_listing: 특정 매물 선택. 예 "A로 할게"
- chitchat: 그 외
규칙: 단위는 만원. edit_condition이면 edit를 반드시 채운다. '입지/통학/밤길/막차/위치' 단어가 있으면 ask_location."""

# --- 추출 엔진 A (solar-pro2) ---
EXTRACT_SCHEMA = {
    "title": "extract_cards",
    "type": "object",
    "properties": {
        "cards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["area", "budget", "safety", "transit", "commute", "kitchen", "light", "security"],
                    },
                    "kind": {"type": "string", "enum": ["hard", "soft"]},
                    "source": {"type": "string", "enum": ["said", "extracted"]},
                    "reason": {
                        "type": "string",
                        "description": "반드시 사용자 발화에서 그대로 인용. 없으면 카드 생성 금지",
                    },
                },
                "required": ["label", "category", "kind", "source", "reason"],
            },
        }
    },
    "required": ["cards"],
}

EXTRACT_SYSTEM = """너는 RoomPilot의 '니즈 통역사'다. 사용자의 생활 발화를 '집 조건 카드'로 번역한다.

[필수 규칙]
1. 지역/학교/회사/동네가 언급되면 반드시 category=area 카드를 만든다(kind=hard, source=said).
2. 보증금/월세가 언급되면 category=budget 카드를 '하나만' 만든다(kind=hard, source=said).
   관리비는 같은 budget 카드 reason에 포함하고, 관리비용 별도 카드를 만들지 마라.
3. 생활 발화에서 도출되는 주거 선호는 kind=soft, source=extracted. (밤귀가→transit, 요리→kitchen 등)
4. 집 자체의 조건이 아닌 사실(본가 위치, 가족 관계, 직업 자체)은 카드를 만들지 마라.
5. 모든 카드 reason에는 근거가 된 사용자 발화를 그대로 인용한다. 근거 없으면 만들지 마라(추측 금지).
6. category는 반드시 다음 중 하나: area, budget, safety, transit, commute, kitchen, light, security.

[예시]
입력: "부산대 신입인데 보증금 1000에 월세 50, 관리비 5~7만 괜찮아요."
→ {label:"지역", category:"area", kind:"hard", source:"said", reason:"부산대 신입"},
   {label:"예산", category:"budget", kind:"hard", source:"said", reason:"보증금 1000 월세 50 관리비 5~7만"}

입력: "밤 11시쯤 들어가요. 본가가 서울이라 자주 못 와요. 요리 자주 해요."
→ {label:"심야 교통", category:"transit", kind:"soft", source:"extracted", reason:"밤 11시쯤 들어가요"},
   {label:"분리형 주방", category:"kitchen", kind:"soft", source:"extracted", reason:"요리 자주 해요"}
   (본가 서울은 집 조건이 아니므로 카드 없음)

입력(역질문 답): "어두운 골목은 무서워요"
→ {label:"야간 안전 동선", category:"safety", kind:"soft", source:"extracted", reason:"어두운 골목은 무서워요"}"""

# --- 점수화 (solar-pro2) ---
SCORE_SCHEMA = {
    "title": "score_listing",
    "type": "object",
    "properties": {
        "breakdown": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "card_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["full", "partial", "none"]},
                    "evidence": {
                        "type": "string",
                        "description": "매물 desc에서 그대로 인용. 없으면 빈 문자열",
                    },
                },
                "required": ["card_id", "status", "evidence"],
            },
        },
        "tradeoff": {"type": "string"},
    },
    "required": ["breakdown"],
}

SCORE_SYSTEM = """매물 설명(desc)이 사용자의 각 주거 조건을 얼마나 충족하는지 '의미 기반'으로 판정한다.

[판정 등급]
- full: 설명에 해당 조건을 충족하는 내용이 분명히 있다.
- partial: 부분적·간접적으로 관련되거나 애매하다.
- none: 설명에 관련 내용이 없거나 오히려 반대다.

[규칙]
1. 키워드가 정확히 일치하지 않아도 '의미'로 판단한다.
   예: "대로변·CCTV·경비 상주" → 야간 안전은 full (사람·불빛·감시가 있으므로).
2. evidence 에는 판정 근거가 된 설명(desc) 문구를 가능한 한 원문 그대로 인용한다.
   근거가 없으면 status=none, evidence="" 로 둔다.
3. 설명에 없는 정보를 지어내지 마라(환각 금지).
4. 주어진 모든 조건(card)에 대해 정확히 하나씩 판정한다. card_id 를 그대로 사용한다.

[예시]
설명: "부산대역 도보 3분, 대로변 오피스텔. CCTV·경비 상주. 개방형 주방. 채광 다소 제한적."
조건: 야간 안전 동선 / 분리형 주방 / 채광·환기
→ 야간 안전 동선: full, evidence="대로변 오피스텔. CCTV·경비 상주"
   분리형 주방: none, evidence=""        (개방형이라 오히려 반대)
   채광·환기: none, evidence=""           ("채광 다소 제한적")"""

# --- Groundedness 판정 (LLM-as-Judge) ---
# Upstage의 groundedness-check 전용 모델이 폐기되어, solar로 근거성을 판정한다(Practice09 Judge LLM).
GROUNDEDNESS_SCHEMA = {
    "title": "groundedness_verdict",
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["grounded", "notGrounded", "notSure"]}
    },
    "required": ["verdict"],
}

GROUNDEDNESS_SYSTEM = """너는 근거성(groundedness) 심판이다. context만을 사실로 삼아 answer를 검증한다.
- grounded: answer의 핵심 주장이 context 문장에서 직접 확인된다(동일 표현/명백한 동의어 포함).
- notGrounded: answer가 context에 없거나 context와 모순된다.
- notSure: context 정보가 부족해 판단 불가.
예) context="남향이라 채광 좋음" / answer="채광 좋음" → grounded
예) context="남향이라 채광 좋음" / answer="방음이 완벽함" → notGrounded
verdict 하나만 출력한다."""
