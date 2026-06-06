# RoomPilot — AI 에이전트 구현 스펙

> 출처: `RoomPilot_데모시나리오.md`("민지의 첫 자취집 찾기")를 **개발 관점**으로 재구성한 백엔드 구현 명세.
> 데모 스크립트의 3-에이전트 구조 · 자율성 범위 · 루프백 · 환각 방지 · 핵심 차별 지표(1:6)를
> LangGraph 그래프 · 상태 스키마 · 프롬프트 · 툴 계약 · API까지 **바로 착수 가능한 수준**으로 풀어 쓴다.

**스택 전제:** Python · FastAPI · LangGraph · **Upstage Solar API**(무료 크레딧)
**범위:** 전체 3-에이전트 + 루프백 (MVP/향후 단계는 §12에 구분 표기)
**매칭 방식:** Solar Embedding 후보 압축 + Solar LLM 가중 점수화 (하이브리드)
**환각 방지:** Upstage Groundedness Check API 게이트 + 근거 인용 강제

---

## 0. 시나리오 → 엔지니어링 매핑

데모의 각 Scene을 구현 단위로 환원한다.

| 데모 Scene | 에이전트 | 구현 단위(노드) | 핵심 산출물 |
|---|---|---|---|
| Scene 1 인터뷰 | Agent 1 | `extract_node` (추출 엔진 A) | 발화 → ConditionCard[] (근거 필수) |
| Scene 2 역질문 | Agent 1 | `discover_node` (발굴 엔진 C) | 사각지대 1개 역질문 + 발굴 카드 |
| Scene 2 우선순위 | Agent 1 | `prioritize_node` (HITL) | 사용자 편집된 가중치 |
| Scene 3 매칭 | Agent 2 | `filter_node` → `embed_rank_node` → `score_node` → `ground_check_node` | ScoredListing[] TOP-N |
| Scene 4 입지 | Agent 3 | `location_node` | LocationAnalysis (카드 관점 번역) |
| Scene 5 루프백 | Graph | `route_after_user` 조건 엣지 | 프로파일 갱신 → 2·3 재실행 |

**검증 지표(코드로 계산):** 직접 발화 카드 수 : 발굴/추출 카드 수 = **1 : N** (목표 1:3~1:6). `NeedsProfile.differentiation_ratio()`로 산출해 응답 메타에 실어 보낸다.

---

## 1. 기술 스택 & 전제

```
Python 3.11+
fastapi / uvicorn        — HTTP + SSE 스트리밍
langgraph                — 상태 그래프 오케스트레이션
langchain-upstage>=0.7.7 — ChatUpstage, UpstageEmbeddings (LLM·임베딩)
httpx                    — Groundedness Check REST 직접 호출(아래 주의)
pydantic v2              — 상태/구조화 출력 스키마
numpy                    — 코사인 유사도
```

**Upstage 모델 ID (직접 `api.upstage.ai` 호출 기준, 하이픈 없음 주의)**

| 용도 | 모델 ID | 비고 |
|---|---|---|
| 추론·점수화·해설 (플래그십) | `solar-pro2` (또는 `solar-pro3`) | tool calling · JSON 구조화 출력 지원 |
| 가벼운 추출/분류 | `solar-mini` | `ChatUpstage` 기본값, 저비용 |
| 임베딩 | `solar-embedding-1-large` | dim 4096, 입력 4096 토큰. `-query`/`-passage` 자동 접미 |
| 환각 검증 | `groundedness-check` | ⚠️ §7.4 주의 — langchain 0.7.7에서 제거됨, REST 직접 호출 |

> ⚠️ **출고 전 검증 필요 항목** (연구 시점 불확실):
> 1. Groundedness Check의 정확한 모델 ID·엔드포인트·반환 문자열 — `console.upstage.ai/docs/capabilities/groundedness-checking`에서 확인.
> 2. `reasoning_effort` 허용값(`low`/`medium`/`high` 버전 드리프트).
> 3. 무료 크레딧 금액(가입 시 $10 추정) — 가입 페이지 확인.

**인증·셋업**

```bash
export UPSTAGE_API_KEY="up_..."        # langchain-upstage가 자동 인식
# OpenAI SDK 호환 베이스 URL: https://api.upstage.ai/v1  (또는 .../v1/solar)
```

---

## 2. 시스템 아키텍처 (LangGraph)

단일 `StateGraph`에 공유 상태(`AgentState`)를 흘려보낸다. 사용자 발화 1턴 = 그래프 1회 실행이 아니라,
**HITL 인터럽트**(`interrupt`)로 카드 확인·우선순위 편집·매물 선택 지점에서 멈췄다 재개한다.

```
                         ┌──────────────────────────────────────────┐
                         │              AgentState (shared)           │
                         └──────────────────────────────────────────┘
   user turn
      │
      ▼
 ┌─────────────┐   더 물을 사각지대 있음
 │ extract     │──────────────┐
 │ (Agent1-A)  │              ▼
 └─────────────┘        ┌─────────────┐   interrupt(역질문)
      │                 │ discover    │────────────────▶ user 응답 → extract 루프
      │ 카드 충분        │ (Agent1-C)  │
      ▼                 └─────────────┘
 ┌─────────────┐ interrupt(우선순위 편집)
 │ prioritize  │◀───────────────────────── user 편집
 │ (Agent1)    │
 └─────────────┘
      │  needs_profile 확정
      ▼
 ┌─────────────┐   ┌──────────────┐   ┌─────────────┐   ┌──────────────────┐
 │ filter      │──▶│ embed_rank   │──▶│ score       │──▶│ ground_check     │
 │ (하드 제약)  │   │ (임베딩 압축) │   │ (LLM 점수화) │   │ (환각 검증 게이트)│
 └─────────────┘   └──────────────┘   └─────────────┘   └──────────────────┘
                                                                  │ TOP-N 확정
                                                                  ▼
                                                          ┌─────────────┐ interrupt(매물 선택/질문)
                                                          │ location    │◀── 상위 후보만 API 호출
                                                          │ (Agent3)    │
                                                          └─────────────┘
                                                                  │
                                                                  ▼
                                                          ┌─────────────┐
                                                          │ respond     │── SSE로 카드/추천/해설 push
                                                          └─────────────┘
                                                                  │
            루프백: user가 조건 수정("월세 +5만") ── route_after_user ──┘
            → needs_profile 갱신 → filter부터 재실행
```

**상태 영속:** LangGraph `MemorySaver`(데모) → 향후 `PostgresSaver`. `thread_id` = 세션 ID.

---

## 3. 공유 상태 스키마 (`AgentState`)

```python
# app/state.py
from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

CardSource = Literal["said", "extracted", "discovered"]   # 직접발화 / 추출 / 발굴
MatchStatus = Literal["full", "partial", "none"]

class ConditionCard(BaseModel):
    id: str
    label: str                       # "야간 안전 동선"
    category: str                    # "safety" | "transit" | "budget" | "kitchen" ...
    kind: Literal["hard", "soft"]    # 🟦하드 / 🟩소프트·🟧발굴
    weight: int = Field(ge=0, le=3)  # ★ 0~3 (우선순위)
    source: CardSource
    reason: str                      # 근거 발화 인용 또는 (추론) 근거 — 환각 방지 핵심
    confidence: float = 1.0

class NeedsProfile(BaseModel):
    cards: list[ConditionCard] = []
    priority_order: list[str] = []   # 카테고리 우선순위 ["safety","budget","commute"]
    hard: dict = {}                  # {deposit, rent, commute_max, area, mgmt_fee_max}

    def said_count(self) -> int:
        return sum(c.source == "said" for c in self.cards)

    def derived_count(self) -> int:  # 추출+발굴
        return sum(c.source != "said" for c in self.cards)

    def differentiation_ratio(self) -> str:   # 핵심 차별 지표 1:N
        s = max(self.said_count(), 1)
        return f"1:{round(self.derived_count() / s)}"

class MatchResult(BaseModel):
    card_id: str
    status: MatchStatus
    evidence: str                    # 매물 설명에서 인용한 근거 문장
    grounded: Optional[bool] = None  # Groundedness Check 결과

class ScoredListing(BaseModel):
    listing_id: str
    score: int
    excluded: bool = False
    breakdown: list[MatchResult] = []
    penalty: int = 0
    tradeoff: Optional[str] = None   # "안전 최상 ↔ 요리 환경 아쉬움"

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    profile: NeedsProfile
    candidates: list[str]            # filter 통과 listing_id
    ranked: list[ScoredListing]      # score 결과 TOP-N
    location_analysis: dict          # Agent3 산출 (listing_id -> LocationAnalysis)
    asked_dimensions: list[str]      # discover가 이미 물은 사각지대(중복 질문 방지)
    stage: Literal["needs","listings","location","done"]
```

> **프론트엔드 계약 정합:** `frontend/src/types.ts`의 `ConditionCard`/`ScoredListing`/`LocationAnalysis`와 1:1 대응.
> 백엔드는 snake_case, 직렬화 시 camelCase로 변환(FastAPI `alias` 또는 응답 매퍼)하여 FE 타입과 일치시킨다.

---

## 4. 시드 데이터 모델 (`Listing`)

`frontend/src/data/listings.ts`의 시드와 동일 스키마를 백엔드 `data/listings.json`으로 미러링한다.
임베딩 매칭의 입력은 **`desc`(매물 설명 텍스트)** — 시나리오의 "설명 텍스트의 의미"가 곧 매칭 대상이다.

```python
class Listing(BaseModel):
    id: str
    name: str                # "A빌라"
    type: str; area: str     # "원룸", "장전동"
    deposit: int; rent: int; mgmt_fee: int = 0
    pyeong: float; floor: int
    options: list[str]
    desc: str                # ★ 의미 매칭 대상 — 시드 설명 전문
    # 입지 원천 데이터(Agent3가 카드 관점으로 번역하기 전 raw)
    geo: dict                # {lat, lng, subway, walk_min, ...}
    embedding: Optional[list[float]] = None   # 사전 계산 캐시(4096-d)
```

데모 매물은 **시드(가상)** 임을 응답 메타에 명시(`"data_source": "seed"`).

---

## 5. Agent 1 「니즈 통역사」

### 5.1 추출 엔진 A — `extract_node`

발화를 ConditionCard로 변환. **근거(발화 인용) 없는 카드 생성 금지**(환각 1차 방어).
Solar의 구조화 출력(JSON schema)으로 강제한다.

```python
# app/agents/needs.py
from langchain_upstage import ChatUpstage

EXTRACT_SCHEMA = {  # response_format=json_schema 로 전달
  "type": "object",
  "properties": {
    "cards": {"type": "array", "items": {
      "type": "object",
      "properties": {
        "label": {"type": "string"},
        "category": {"type": "string",
            "enum": ["area","budget","safety","transit","commute","kitchen","light","security"]},
        "kind": {"type": "string", "enum": ["hard","soft"]},
        "source": {"type": "string", "enum": ["said","extracted"]},
        "reason": {"type": "string",
            "description": "반드시 사용자 발화에서 그대로 인용. 없으면 카드 생성 금지"}
      },
      "required": ["label","category","kind","source","reason"]
    }}
  }, "required": ["cards"]
}

EXTRACT_SYSTEM = """너는 RoomPilot의 '니즈 통역사'다.
사용자의 생활 발화를 '집 조건 카드'로 번역한다.
규칙:
1. 직접 말한 사실(지역/예산 등)은 source=said, kind=hard.
2. 생활 발화에서 도출되는 조건(예: "밤 11시 귀가"→심야교통)은 source=extracted, kind=soft.
3. 모든 카드의 reason에는 근거가 된 사용자 발화를 그대로 인용한다.
4. 발화에 근거가 없으면 카드를 만들지 마라. 추측 금지.
예) "밤 11시쯤 집에 들어가요" → {label:"심야 교통", category:"transit",
    kind:"soft", source:"extracted", reason:"밤 11시쯤 집에 들어가요"}"""

llm_pro = ChatUpstage(model="solar-pro2", temperature=0.2)
```

`extract_node`는 신규 카드를 `profile.cards`에 병합(중복 label은 confidence 갱신)한다.

### 5.2 발굴 엔진 C — `discover_node`

**사각지대 체크리스트** 중 아직 안 채워진 차원에서 **가장 중요한 1개만** 질문(설문화 방지).

```python
BLIND_SPOT_CHECKLIST = [
    ("safety",   "야간 단독 귀가 동선 안전"),
    ("security", "택배·공동현관 보안"),
    ("light",    "채광·환기·습기(곰팡이)"),
    ("noise",    "방음"),
    ("kitchen",  "주방 분리/환기"),
]

def pick_blind_spot(state) -> Optional[tuple]:
    have = {c.category for c in state["profile"].cards}
    asked = set(state["asked_dimensions"])
    for cat, desc in BLIND_SPOT_CHECKLIST:
        if cat not in have and cat not in asked:
            return cat, desc      # 우선순위 순서대로 1개
    return None
```

- 발굴 질문은 **공감 + 근거("첫 자취생이 제일 후회하는 부분")** 형식. → `discover_node`가 `interrupt()`로 사용자 응답 대기.
- 사용자가 동의하면 **발굴 카드**(`source="discovered"`, `kind="soft"`, `reason="(추론) ..."`)를 추가.
- 발굴 카드의 reason은 `(추론)` 접두 — UI에서 🟧로 구분, 환각 검증에서 별도 취급.

### 5.3 우선순위 편집 — `prioritize_node` (HITL)

```python
from langgraph.types import interrupt
def prioritize_node(state):
    payload = interrupt({              # FE에 우선순위 편집 UI 요청
        "type": "edit_priority",
        "categories": list({c.category for c in state["profile"].cards if c.kind=="soft"})
    })
    state["profile"].priority_order = payload["order"]   # 예: ["safety","budget","commute"]
    # 우선순위→가중치 반영: 1순위 weight=3, 2순위=2, ...
    return state
```

### 5.4 차별 지표 노출

`extract`/`discover` 종료 시 `profile.differentiation_ratio()`를 계산해 SSE 이벤트(`metric`)로 push → FE 상단 배지("1:6").

---

## 6. Agent 2 「매물 큐레이터」 (하이브리드 매칭)

### 6.1 `filter_node` — 하드 제약 압축

순수 함수(LLM 미사용). 시나리오 "42건 → 9건".

```python
def filter_node(state):
    h = state["profile"].hard
    state["candidates"] = [
        L.id for L in load_listings()
        if L.area_matches(h["area"])
        and L.deposit <= h["deposit"]
        and L.rent <= h["rent"] + h.get("mgmt_fee_max", 0)
    ]
    return state
```

### 6.2 `embed_rank_node` — 임베딩 후보 압축

소프트 카드 묶음과 매물 `desc`의 의미 유사도로 1차 정렬(상위 K만 LLM 점수화로 넘김 → 비용 절감).

```python
from langchain_upstage import UpstageEmbeddings
import numpy as np
emb = UpstageEmbeddings(model="solar-embedding-1-large")  # 접미사 자동

def embed_rank_node(state, K=6):
    cards = [c for c in state["profile"].cards if c.kind == "soft"]
    query = " / ".join(f"{c.label}: {c.reason}" for c in cards)
    qv = np.array(emb.embed_query(query))                 # -query
    scored = []
    for lid in state["candidates"]:
        L = get_listing(lid)
        dv = np.array(L.embedding or emb.embed_documents([L.desc])[0])  # -passage, 캐시
        scored.append((lid, float(qv @ dv / (np.linalg.norm(qv)*np.linalg.norm(dv)))))
    state["candidates"] = [lid for lid, _ in sorted(scored, key=lambda x:-x[1])[:K]]
    return state
```

> 매물 임베딩은 **사전 계산**해 `listings.json`에 캐시(`embedding`). 시드가 고정이므로 1회만.

### 6.3 `score_node` — LLM 가중 점수화 + 근거 인용

각 후보를 카드별로 `full/partial/none` 판정하고 **매물 설명에서 근거 문장을 인용**. 가중치 합산 점수.

```python
SCORE_SCHEMA = {
  "type":"object","properties":{
    "breakdown":{"type":"array","items":{"type":"object","properties":{
      "card_id":{"type":"string"},
      "status":{"type":"string","enum":["full","partial","none"]},
      "evidence":{"type":"string","description":"매물 desc에서 그대로 인용. 없으면 빈 문자열"}
    },"required":["card_id","status","evidence"]}},
    "tradeoff":{"type":"string"}
  },"required":["breakdown"]
}

SCORE_SYSTEM = """매물 설명 텍스트와 사용자 카드를 대조해 카드별 충족도를 판정한다.
규칙:
1. 판정 근거(evidence)는 반드시 매물 설명(desc)에서 그대로 인용한다.
2. 설명에 없는 정보는 추론하지 말고 status=none, evidence="" 로 둔다. (환각 금지)
3. 1순위 카드 충족이 점수에 가장 크게 기여하도록 가중한다."""
```

**점수 계산(코드):** `score = Σ(weight × {full:1, partial:0.5, none:0}) / Σweight × 100 − penalty`.
1순위 카드 미충족 시 penalty 가산. 결과는 `ScoredListing`로 `state["ranked"]`(TOP-3).

### 6.4 `ground_check_node` — 환각 검증 게이트 ⚠️

LLM이 인용한 `evidence`가 **실제 매물 설명에 근거**하는지 Upstage Groundedness Check로 검증.
`notGrounded` 판정 evidence는 폐기하고 해당 카드를 `status=none`으로 강등 → 점수 재계산.

```python
# app/upstage/groundedness.py
# 주의: langchain-upstage 0.7.7에는 UpstageGroundednessCheck가 없음 → REST 직접 호출
import os, httpx

def check_grounded(context: str, answer: str) -> str:
    """returns 'grounded' | 'notGrounded' | 'notSure'  (출고 전 엔드포인트/반환값 검증 필요)"""
    r = httpx.post(
        "https://api.upstage.ai/v1/solar/chat/completions",   # ⚠️ 정확 경로 docs 확인
        headers={"Authorization": f"Bearer {os.environ['UPSTAGE_API_KEY']}"},
        json={"model": "groundedness-check",
              "messages": [{"role":"user","content":context},
                           {"role":"assistant","content":answer}]},
        timeout=20,
    )
    return r.json()["choices"][0]["message"]["content"]

def ground_check_node(state):
    for sl in state["ranked"]:
        desc = get_listing(sl.listing_id).desc
        for m in sl.breakdown:
            if m.evidence:
                m.grounded = check_grounded(desc, m.evidence) == "grounded"
                if not m.grounded:           # 근거 미확인 → 강등
                    m.status, m.evidence = "none", ""
        recompute_score(sl)                  # 강등 반영 재계산
    state["ranked"].sort(key=lambda s: -s.score)
    return state
```

> **사용자 질문이 설명에 없는 정보일 때**(예: "C 방음 어때요?"): `score_node`가 `status=none, evidence=""`로 두고,
> `respond_node`가 *"설명에 정보가 없어 지어내지 않습니다 — 입주 전 직접 확인 항목으로 체크"* 문구를 생성(시나리오 §4 환각 방지 동작).

---

## 7. Agent 3 「입지 해설사」 — `location_node`

상위 후보(A·B)만 지도/공공데이터 **툴 호출**, 나머지는 캐시. 입지 raw 데이터를 *사용자 카드 관점*으로 번역.

```python
# 외부 API는 툴로 추상화(데모는 스텁/시드, 실연동은 향후)
@tool
def get_transit_info(listing_id: str) -> dict:
    """막차 시간, 역→집 도보, 경로 밝기. (데모: 시드 geo 기반 스텁)"""

@tool
def get_commute_info(listing_id: str) -> dict:
    """집→캠퍼스 도보/대중교통 환산."""
```

`location_node`는 `solar-pro2`에 **카드(우선순위 포함) + 툴 결과**를 주고,
`LocationAnalysis`(commute/nightSafety/convenience/basis/pros/cons/aiComment/scoreBreakdown — FE 타입과 동일)를 생성.
해설은 반드시 **카드 관점**("민지님 1순위 안전 카드 기준…")으로 서술.

- **상위 N(기본 2)만 실시간 호출**, 결과 `location_analysis[listing_id]`에 캐시.
- 입지 수치는 데모용 가정값임을 메타에 표기.

---

## 8. 루프백 (조건 수정 → 재추천)

사용자가 조건을 바꾸면("월세 +5만") 프로파일 갱신 후 **filter부터 재실행**. LangGraph 조건 엣지로 표현.

```python
def route_after_user(state) -> str:
    last = state["messages"][-1].content
    intent = classify_intent(last)     # solar-mini: edit_condition | select | ask | done
    if intent == "edit_condition":
        apply_condition_edit(state, last)   # 예: rent 50→55
        return "filter"                     # Agent2·3 자동 재실행
    if intent == "ask":
        return "respond"
    return "location" if state["stage"]=="listings" else "respond"

graph.add_conditional_edges("respond", route_after_user,
    {"filter":"filter", "location":"location", "respond":"respond", END:END})
```

재실행 시 응답에 **변화 델타**("9건→14건", "D신축빌라 신규 1위, +5만으로 채광·엘리베이터 확보, 연 48만원 추가")를 포함 → 시나리오 §6의 "두 갈래 선택" 제시.

---

## 9. 환각 방지 종합 전략 (4중 방어)

| 계층 | 위치 | 메커니즘 |
|---|---|---|
| 1. 생성 제약 | extract/score 프롬프트 | 근거 인용 필수, 없으면 카드/판정 생성 금지 |
| 2. 구조 강제 | response_format=json_schema | `reason`/`evidence` 필드 필수화 |
| 3. 사후 검증 | `ground_check_node` | Groundedness Check로 evidence 실근거 확인, 미근거 강등 |
| 4. 미지 정보 처리 | respond | 설명에 없는 질문 → "지어내지 않음 + 직접 확인 항목" 전환 |

발굴 카드(`source=discovered`)는 의도된 추론이므로 `reason`에 `(추론)` 명시 + 사용자 동의(HITL)를 거쳐 환각과 구분.

---

## 10. API 설계 (FastAPI)

카드/추천/해설이 **실시간으로 채워지는** UX이므로 SSE 스트리밍.

```
POST /session                      → {session_id}                  세션 생성(thread_id)
POST /session/{id}/message         → SSE stream                    사용자 발화 처리
        event: card     data: ConditionCard            (extract/discover)
        event: metric   data: {ratio:"1:6", said:2, derived:6}
        event: question data: {type:"discover"|"edit_priority"|"select"}  ← interrupt
        event: ranked   data: ScoredListing[]          (score 후)
        event: location data: LocationAnalysis
        event: message  data: {role:"ai", text}
        event: done
POST /session/{id}/resume          → SSE stream         interrupt 응답(우선순위/매물선택)
GET  /session/{id}/profile         → NeedsProfile
```

LangGraph `astream`(`stream_mode="updates"`) 출력을 SSE 이벤트로 매핑. `interrupt` 발생 시 `question` 이벤트로 FE에 입력 요청 → `/resume`로 `Command(resume=...)` 재개.

---

## 11. 프로젝트 구조

```
backend/
  app/
    main.py                 FastAPI 앱 · SSE 라우트
    graph.py                StateGraph 조립 · 엣지 정의
    state.py                AgentState · NeedsProfile · 스키마(§3)
    agents/
      needs.py              extract_node · discover_node · prioritize_node (Agent1)
      curator.py            filter · embed_rank · score · ground_check (Agent2)
      location.py           location_node (Agent3)
      router.py             route_after_user · classify_intent (루프백)
    upstage/
      llm.py                ChatUpstage 팩토리(모델별)
      embeddings.py         UpstageEmbeddings 래퍼
      groundedness.py       Groundedness Check REST(§6.4)
    data/
      listings.json         시드 매물(+사전계산 embedding)
      seed_embeddings.py    임베딩 1회 사전계산 스크립트
    tools/
      geo.py                입지 툴(데모 스텁 → 향후 실 API)
  tests/
    test_needs.py  test_curator.py  test_groundedness.py  test_graph.py
  requirements.txt
  .env.example              UPSTAGE_API_KEY=
```

**테스트 우선순위(순수 로직):** `filter_node` · 점수 계산 · `differentiation_ratio` · 임베딩 코사인 · 루프백 라우팅. LLM 노드는 응답 모킹.

---

## 12. 구현 단계 (MVP → 전체)

| 단계 | 범위 | 시나리오 대응 | 게이트 |
|---|---|---|---|
| **M1 (MVP 핵심)** | state + extract + discover + prioritize + filter + embed_rank + score + 1:6 지표 | Scene 1~4 | 민지 스크립트 E2E 시연 |
| **M2** | ground_check_node(환각 검증) + 미지정보 처리 | Scene 4 환각 방지 | Groundedness 게이트 통과 |
| **M3** | location_node(Agent3) + 입지 툴 스텁 | Scene 4(입지 해설) | 카드 관점 해설 생성 |
| **M4 (전체)** | 루프백(route_after_user) + 재추천 델타 | Scene 5 | "월세+5만" 재랭킹 동작 |
| 향후 | 실매물·실 지도/치안 API · 로그인/영속(Postgres) · 정밀 치안 데이터 | — | — |

> MVP 데모 1차 목표는 **민지 시나리오(Scene 1~4)를 매끄럽게 시연** — 기획서 범위와 일치.

---

## 13. 출고 전 검증 체크리스트 (Upstage 불확실 항목)

- [ ] Groundedness Check: 모델 ID·엔드포인트·반환 문자열(`grounded`/`notGrounded`/`notSure`) 라이브 확인 (`langchain-upstage` 0.7.7에 없음 → REST)
- [ ] `solar-pro2` vs `solar-pro3` 가용성·`reasoning_effort` 허용값 확인
- [ ] `response_format=json_schema` 스키마 준수율 실측(미준수 시 재시도/파서 폴백)
- [ ] 무료 크레딧 잔량·요금(Solar Pro $0.15/1M in, $0.60/1M out / 임베딩 $0.10/1M) 기준 예산 산정
- [ ] FE 타입(`types.ts`)과 응답 JSON(camelCase) 정합 검증
```
