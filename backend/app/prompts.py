"""시스템 프롬프트 + 구조화 출력 스키마 (구현스펙 §5, §6 / 오케스트레이션 §2).

환각 방지의 핵심: reason/evidence 를 필수 필드로 두어 '근거 없는 카드/판정'을 구조로 차단한다.
"""

# --- 의도 분류 (solar-mini) ---
INTENT_SCHEMA = {
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
- provide_info: 생활/조건 정보를 새로 말함 (니즈 단계)
- edit_condition: 기존 조건을 바꿈. 예 "월세 5만 더"→{field:rent,op:inc,value:5}, "예산을 60으로"→{op:set,value:60}
- ask_listing: 추천 매물에 대한 질문 ("C 방음 어때요?")
- ask_location: 입지/통학/밤길 질문
- select_listing: 특정 매물 선택
- chitchat: 그 외
단위는 만원. 조건 변경이면 edit를 반드시 채운다."""

# --- 추출 엔진 A (solar-pro2) ---
EXTRACT_SCHEMA = {
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

EXTRACT_SYSTEM = """너는 RoomPilot의 '니즈 통역사'다.
사용자의 생활 발화를 '집 조건 카드'로 번역한다.
규칙:
1. 직접 말한 사실(지역/예산 등)은 source=said, kind=hard.
2. 생활 발화에서 도출되는 조건(예: "밤 11시 귀가"→심야교통)은 source=extracted, kind=soft.
3. 모든 카드의 reason에는 근거가 된 사용자 발화를 그대로 인용한다.
4. 발화에 근거가 없으면 카드를 만들지 마라. 추측 금지."""

# --- 점수화 (solar-pro2) ---
SCORE_SCHEMA = {
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

SCORE_SYSTEM = """매물 설명 텍스트와 사용자 카드를 대조해 카드별 충족도를 판정한다.
규칙:
1. 판정 근거(evidence)는 반드시 매물 설명(desc)에서 그대로 인용한다.
2. 설명에 없는 정보는 추론하지 말고 status=none, evidence="" 로 둔다. (환각 금지)
3. 1순위 카드 충족이 점수에 가장 크게 기여하도록 가중한다."""
