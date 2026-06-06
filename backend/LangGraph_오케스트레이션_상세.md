# RoomPilot — LangGraph 오케스트레이션 상세

> `AI_에이전트_구현스펙.md`의 §2~§8을 **실행 가능한 graph.py 수준**으로 확장한 문서.
> 노드 시그니처, 리듀서, `interrupt`/`Command(resume)` HITL 흐름, 조건 엣지, 루프백,
> 의도 분류·조건 편집 파싱, SSE 스트리밍 연동까지 그대로 옮겨 적을 수 있게 다룬다.
>
> 대상 버전: `langgraph>=0.2.x` (`interrupt`, `Command`, `get_stream_writer`, `MemorySaver` 기준).

---

## 0. 전체 토폴로지

핵심은 **진입 라우터(`ingest`)** 하나로 모든 턴을 받고, 단계(`stage`)와 의도(intent)로 분기하는 것이다.
HITL 지점 3곳(역질문 / 우선순위 / 매물선택)은 `interrupt()`로 멈췄다 `Command(resume=...)`로 재개한다.

```
                                  START
                                    │
                                    ▼
                            ┌───────────────┐
                            │    ingest      │  (의도 분류 · stage 확인)
                            └───────────────┘
        stage=needs │  intent=edit │ intent=ask │ intent=select/ask-loc
                    ▼              ▼            ▼            ▼
              ┌─────────┐   apply_edit→filter  respond   location
              │ extract │
              └─────────┘
            blind spot? │ 있음           │ 없음
                        ▼                ▼
                  ┌──────────┐     ┌────────────┐
                  │ discover │     │ prioritize │  ← interrupt(우선순위 편집)
                  │ ⏸interrupt│     └────────────┘
                  └──────────┘            │
                        │ resume          ▼
                        └──▶ extract   ┌────────┐   ┌───────────┐   ┌────────┐   ┌──────────────┐
                                       │ filter │──▶│ embed_rank │──▶│ score  │──▶│ ground_check │
                                       └────────┘   └───────────┘   └────────┘   └──────────────┘
                                                                                        │
                                                                                        ▼
                                                                                  ┌──────────┐
                                                                                  │ respond  │──▶ END
                                                                                  └──────────┘
                                       ┌──────────┐
        intent=select/ask-location ──▶ │ location │ ── interrupt(매물 선택) ──▶ respond ──▶ END
                                       └──────────┘
```

**핵심 설계 원칙**
1. **한 턴 = `graph.stream(...)` 1회.** 새 발화는 `{"messages":[msg]}`로 `START`부터, interrupt 재개는 `Command(resume=payload)`로 멈춘 노드부터.
2. **노드는 부분 상태 업데이트(dict)를 반환** → 리듀서가 병합. 전체 state를 복사·반환하지 않는다.
3. **카드/추천은 `get_stream_writer()` 커스텀 이벤트**로 즉시 흘려보내 "실시간으로 채워지는" UX를 만든다.
4. **루프백은 `ingest`의 `edit` 분기**로 일원화 — `filter`부터 재실행.

---

## 1. 상태 + 리듀서 (`state.py` 보강)

§3의 `AgentState`에 **카드 병합 리듀서**와 단계 필드를 더한다. 카드는 매 노드가 누적하므로
교체가 아니라 **upsert 병합**이 필요하다.

```python
# app/state.py  (구현스펙 §3에 이어서)
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

def merge_cards(existing: list[ConditionCard],
                new: list[ConditionCard]) -> list[ConditionCard]:
    """label 기준 upsert. 같은 label 재등장 시 confidence·근거 갱신, source 승격(said>discovered>extracted 보존)."""
    by_label = {c.label: c for c in existing}
    for c in new:
        prev = by_label.get(c.label)
        if prev is None:
            by_label[c.label] = c
        else:
            # 직접 발화가 추론을 덮어쓸 수 있게(반대는 금지)
            if prev.source != "said" and c.source == "said":
                prev.source, prev.kind = "said", c.kind
            prev.confidence = max(prev.confidence, c.confidence)
            if c.reason:
                prev.reason = c.reason
    return list(by_label.values())

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    cards: Annotated[list[ConditionCard], merge_cards]   # ★ 리듀서로 누적
    hard: dict                          # 하드 제약(deposit/rent/area/mgmt_fee_max/commute_max)
    priority_order: list[str]
    candidates: list[str]
    ranked: list[ScoredListing]
    location_analysis: dict
    asked_dimensions: list[str]
    stage: str                          # "needs" | "listings" | "location" | "done"
    intent: str                         # ingest가 채움
```

> `NeedsProfile`(구현스펙 §3)는 `cards`+`hard`+`priority_order`를 감싼 헬퍼로 유지하되, 그래프 상태에서는
> 평탄화해 리듀서를 명확히 건다. `differentiation_ratio()`는 `cards`만으로 계산 가능.

**체크포인터 & 스레드**

```python
# app/graph.py
from langgraph.checkpoint.memory import MemorySaver   # 데모. 향후 PostgresSaver
checkpointer = MemorySaver()
# 호출 시 config = {"configurable": {"thread_id": session_id}}
```

---

## 2. 진입 라우터 `ingest` — 의도 분류

모든 턴의 입구. 마지막 사용자 메시지로 의도를 분류(`solar-mini`, 구조화 출력)하고 `stage`와 함께 분기 키를 만든다.

```python
# app/agents/router.py
from langchain_upstage import ChatUpstage
from langgraph.types import Command

llm_mini = ChatUpstage(model="solar-mini", temperature=0)

INTENT_SCHEMA = {
  "type": "object",
  "properties": {
    "intent": {"type": "string",
       "enum": ["chitchat","provide_info","edit_condition","ask_listing","select_listing","ask_location"]},
    "edit": {  # edit_condition일 때만
      "type": "object",
      "properties": {
        "field": {"type": "string", "enum": ["rent","deposit","commute_max","area","mgmt_fee_max"]},
        "op": {"type": "string", "enum": ["set","inc","dec"]},
        "value": {"type": "number"}
      }
    }
  }, "required": ["intent"]
}

INTENT_SYSTEM = """사용자의 마지막 발화 의도를 분류한다.
- provide_info: 생활/조건 정보를 새로 말함 (니즈 단계)
- edit_condition: 기존 조건을 바꿈. 예 "월세 5만 더"→{field:rent,op:inc,value:5}, "예산을 60으로"→{op:set,value:60}
- ask_listing: 추천 매물에 대한 질문 ("C 방음 어때요?")
- ask_location: 입지/통학/밤길 질문
- select_listing: 특정 매물 선택
- chitchat: 그 외
단위는 만원. 조건 변경이면 edit를 반드시 채운다."""

def ingest_node(state: AgentState):
    last = state["messages"][-1].content
    out = llm_mini.with_structured_output(INTENT_SCHEMA).invoke(
        [{"role":"system","content":INTENT_SYSTEM},{"role":"user","content":last}])
    update = {"intent": out["intent"]}
    if out["intent"] == "edit_condition" and out.get("edit"):
        update["hard"] = apply_condition_edit(dict(state["hard"]), out["edit"])
    return update

def apply_condition_edit(hard: dict, edit: dict) -> dict:
    f, op, v = edit["field"], edit["op"], edit.get("value", 0)
    if f in ("area",):                 # 비수치 필드는 set만
        hard[f] = v
    elif op == "set": hard[f] = v
    elif op == "inc": hard[f] = hard.get(f, 0) + v
    elif op == "dec": hard[f] = hard.get(f, 0) - v
    return hard            # 예: 월세 50→55  ("월세 +5만" 루프백)
```

**`ingest` 분기 함수**

```python
def route_from_ingest(state: AgentState) -> str:
    if state["stage"] == "needs":
        return "extract"                       # 아직 니즈 수집 중
    i = state["intent"]
    if i == "edit_condition":   return "filter"     # 루프백: 재추천
    if i == "select_listing":   return "location"
    if i == "ask_location":     return "location"
    if i in ("ask_listing","chitchat"): return "respond"
    return "extract"                           # provide_info 등
```

---

## 3. 니즈 단계 — extract / discover / prioritize

### 3.1 `extract_node` + 분기

추출 후 사각지대가 남았는지로 분기. 발화 근거 카드만 생성(구현스펙 §5.1).

```python
# app/agents/needs.py
from langgraph.config import get_stream_writer

MAX_DISCOVER = 3   # 설문화 방지: 발굴 역질문 최대 횟수

def extract_node(state: AgentState):
    last = state["messages"][-1].content
    result = llm_pro.with_structured_output(EXTRACT_SCHEMA).invoke(
        [{"role":"system","content":EXTRACT_SYSTEM},{"role":"user","content":last}])
    new_cards = [to_card(c) for c in result["cards"]]

    writer = get_stream_writer()               # 카드 즉시 push (실시간 채움)
    for c in new_cards:
        writer({"type": "card", "card": c.model_dump(by_alias=True)})

    # 하드 카드는 hard dict에도 반영
    hard = dict(state["hard"])
    for c in new_cards:
        if c.kind == "hard":
            hard.update(card_to_hard(c))       # 예산/지역/관리비 → hard

    ratio = differentiation_ratio(state["cards"] + new_cards)
    writer({"type": "metric", **ratio})        # FE 상단 1:6 배지
    return {"cards": new_cards, "hard": hard}   # 리듀서가 누적 병합

def route_after_extract(state: AgentState) -> str:
    asked = len(state["asked_dimensions"])
    if asked < MAX_DISCOVER and pick_blind_spot(state) is not None:
        return "discover"
    return "prioritize"                        # 사각지대 소진 → 우선순위 편집
```

### 3.2 `discover_node` — interrupt로 역질문

사각지대 1개를 골라 `interrupt`로 질문을 던지고 멈춘다. 사용자가 답하면 `extract`로 돌아가 그 답을 카드화한다.

```python
from langgraph.types import interrupt

def discover_node(state: AgentState):
    cat, desc = pick_blind_spot(state)          # 미충족 차원 1개 (구현스펙 §5.2)
    question = build_discover_question(cat, desc, state)   # 공감+근거 형 질문 생성(LLM 또는 템플릿)

    # ⏸ 여기서 멈춘다. payload가 FE로 흘러가고, resume 값이 반환된다.
    answer = interrupt({
        "type": "discover_question",
        "category": cat,
        "text": question,        # "밤 11시에 혼자 들어가는 길… 골목 무서운 거 신경 쓰세요?"
    })

    # resume 후 실행 재개: 사용자의 답을 메시지에 싣고 asked에 기록 → extract가 처리
    return {
        "messages": [{"role": "user", "content": answer}],
        "asked_dimensions": state["asked_dimensions"] + [cat],
    }

# discover → extract 로 무조건 복귀 (그 답을 카드로 추출)
# graph.add_edge("discover", "extract")
```

> **중복 질문 방지:** `asked_dimensions`에 물은 차원을 누적, `pick_blind_spot`이 `have ∪ asked`를 제외하고 고른다.
> **`interrupt` 동작:** 노드 진입 시점부터 재실행되므로, `interrupt` **앞에 부수효과를 두지 말 것**(재개 시 재실행됨). 부수효과는 `interrupt` 이후에.

### 3.3 `prioritize_node` — interrupt로 우선순위 편집

```python
def prioritize_node(state: AgentState):
    soft_cats = sorted({c.category for c in state["cards"] if c.kind == "soft"})
    order = interrupt({"type": "edit_priority", "categories": soft_cats})   # ⏸ FE 편집 UI

    # resume: 사용자가 정렬한 순서로 가중치 부여 (1순위=3 … )
    weights = {cat: max(3 - idx, 1) for idx, cat in enumerate(order["order"])}
    cards = [c.model_copy(update={"weight": weights.get(c.category, c.weight)})
             for c in state["cards"]]
    return {"priority_order": order["order"], "cards": cards, "stage": "listings"}

# prioritize → filter 로 진행
```

---

## 4. 매물 파이프라인 — filter → embed_rank → score → ground_check

직선 파이프라인. 각 노드는 부분 업데이트만 반환(구현스펙 §6 로직 재사용). 마지막에 `respond`로.

```python
# app/agents/curator.py — 노드 시그니처만 (로직은 구현스펙 §6)
def filter_node(state):      return {"candidates": hard_filter(state["hard"])}
def embed_rank_node(state):  return {"candidates": embed_rank(state["candidates"], state["cards"])}

def score_node(state):
    ranked = score_listings(state["candidates"], state["cards"], state["priority_order"])
    writer = get_stream_writer()
    writer({"type": "ranked", "ranked": [r.model_dump(by_alias=True) for r in ranked]})
    return {"ranked": ranked}

def ground_check_node(state):
    ranked = ground_check(state["ranked"])     # 미근거 evidence 강등 후 재정렬 (구현스펙 §6.4)
    writer = get_stream_writer()
    writer({"type": "ranked", "ranked": [r.model_dump(by_alias=True) for r in ranked],
            "grounded": True})
    return {"ranked": ranked}

# add_edge: prioritize/ingest(edit) → filter → embed_rank → score → ground_check → respond
```

**루프백 시 델타 계산** — `respond_node`가 직전 `ranked`와 비교해 "9건→14건, D신축빌라 신규 1위" 같은 변화 문구 생성.

```python
def respond_node(state: AgentState):
    text = compose_reply(state)     # intent별 답변(추천 요약 / 입지 해설 / 환각-회피 문구 / 루프백 델타)
    writer = get_stream_writer()
    writer({"type": "message", "role": "ai", "text": text})
    return {"messages": [{"role": "assistant", "content": text}],
            "stage": "location" if state["ranked"] else state["stage"]}
```

---

## 5. 입지 단계 — `location_node` (interrupt 매물 선택)

상위 후보만 툴 호출(구현스펙 §7). 사용자가 매물을 아직 안 골랐으면 `interrupt`로 선택 요청.

```python
def location_node(state: AgentState):
    sel = current_selection(state)             # 직전 select_listing 또는 TOP-1
    if sel is None:
        sel = interrupt({"type": "select_listing",        # ⏸ "어느 집을 더 볼까요?"
                         "options": [r.listing_id for r in state["ranked"][:3]]})["listing_id"]

    cached = state["location_analysis"]
    if sel not in cached:                        # 상위 후보만 실시간, 나머지 캐시
        cached = {**cached, sel: analyze_location(sel, state["cards"], state["priority_order"])}
    writer = get_stream_writer()
    writer({"type": "location", "listing_id": sel,
            "analysis": cached[sel].model_dump(by_alias=True)})
    return {"location_analysis": cached}
# location → respond
```

---

## 6. 그래프 조립 (`graph.py` 전문)

```python
# app/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.state import AgentState
from app.agents.router import ingest_node, route_from_ingest
from app.agents.needs import (extract_node, route_after_extract,
                              discover_node, prioritize_node)
from app.agents.curator import (filter_node, embed_rank_node, score_node,
                                ground_check_node, respond_node)
from app.agents.location import location_node

def build_graph():
    g = StateGraph(AgentState)
    for name, fn in {
        "ingest": ingest_node, "extract": extract_node, "discover": discover_node,
        "prioritize": prioritize_node, "filter": filter_node, "embed_rank": embed_rank_node,
        "score": score_node, "ground_check": ground_check_node,
        "location": location_node, "respond": respond_node,
    }.items():
        g.add_node(name, fn)

    g.add_edge(START, "ingest")
    g.add_conditional_edges("ingest", route_from_ingest,
        {"extract":"extract", "filter":"filter", "location":"location", "respond":"respond"})

    g.add_conditional_edges("extract", route_after_extract,
        {"discover":"discover", "prioritize":"prioritize"})
    g.add_edge("discover", "extract")            # 역질문 답 → 재추출 (루프)
    g.add_edge("prioritize", "filter")

    g.add_edge("filter", "embed_rank")
    g.add_edge("embed_rank", "score")
    g.add_edge("score", "ground_check")
    g.add_edge("ground_check", "respond")

    g.add_edge("location", "respond")
    g.add_edge("respond", END)
    return g.compile(checkpointer=MemorySaver())

GRAPH = build_graph()
```

**초기 상태**(세션 생성 시):

```python
INIT_STATE = {"messages": [], "cards": [], "hard": {}, "priority_order": [],
              "candidates": [], "ranked": [], "location_analysis": {},
              "asked_dimensions": [], "stage": "needs", "intent": ""}
```

---

## 7. 실행·재개 흐름 (서버 글루)

핵심: **이번 호출이 새 발화인가, interrupt 재개인가**를 `get_state().next`로 판별한다.

```python
# app/runtime.py
from langgraph.types import Command
from app.graph import GRAPH

def has_pending_interrupt(config) -> bool:
    snap = GRAPH.get_state(config)
    return bool(snap.next)            # 멈춘 노드가 있으면 next에 노드명이 들어있음

async def run_turn(session_id: str, user_text: str | None, resume_payload=None):
    config = {"configurable": {"thread_id": session_id}}
    if resume_payload is not None and has_pending_interrupt(config):
        graph_input = Command(resume=resume_payload)          # interrupt 재개
    else:
        graph_input = {"messages": [{"role": "user", "content": user_text}]}  # 새 턴

    async for mode, chunk in GRAPH.astream(graph_input, config,
                                           stream_mode=["custom", "updates"]):
        if mode == "custom":                 # get_stream_writer로 emit한 카드/추천/메시지
            yield chunk                       # → SSE 그대로 전달
        elif mode == "updates":
            # 노드 종료 업데이트. __interrupt__ 키가 있으면 HITL 질문 발생
            for node, payload in chunk.items():
                if node == "__interrupt__":
                    yield {"type": "question", **payload[0].value}   # FE에 입력 요청
```

**FastAPI 엔드포인트 매핑**

```python
@app.post("/session/{sid}/message")     # 새 발화
async def message(sid: str, body: MsgIn):
    return EventSourceResponse(sse(run_turn(sid, body.text)))

@app.post("/session/{sid}/resume")      # interrupt 응답(우선순위/매물선택/역질문 답)
async def resume(sid: str, body: ResumeIn):
    return EventSourceResponse(sse(run_turn(sid, None, resume_payload=body.payload)))
```

- `discover`의 역질문 답: `resume_payload = "어두운 골목은 무서워요"` (문자열) → `interrupt()`가 그 문자열 반환.
- `prioritize` 응답: `resume_payload = {"order": ["safety","budget","commute"]}`.
- `location`의 선택: `resume_payload = {"listing_id": "A"}`.

---

## 8. SSE 이벤트 계약 (FE 연동)

`get_stream_writer` 커스텀 + `__interrupt__`가 모두 한 스트림으로 나간다.

| event `type` | 발생 노드 | payload | FE 동작 |
|---|---|---|---|
| `card` | extract | ConditionCard | 우측 카드 패널 실시간 추가 |
| `metric` | extract | `{ratio,"said","derived"}` | 상단 1:6 배지 |
| `question` | discover/prioritize/location | `{type, ...}` | 입력 UI 띄움 → `/resume` |
| `ranked` | score/ground_check | ScoredListing[] | 추천 리스트(점수 갱신) |
| `location` | location | `{listing_id, analysis}` | 입지 해설 패널 |
| `message` | respond | `{role,text}` | 채팅 말풍선 |
| `done` | 스트림 종료 | — | 입력 활성화 |

---

## 9. 동작 트레이스 (민지 시나리오 매핑)

| 턴 | 입력 | 경로 | interrupt | 산출 |
|---|---|---|---|---|
| 1 | "부산대 신입, 보 1000 월 50" | ingest(needs)→extract→prioritize? | — | 하드카드 3 (지역/예산/관리비) |
| 2 | "밤 11시 귀가, 본가 멀어요, 요리 자주" | extract→discover | ⏸ 야간안전 역질문 | 소프트카드 + 역질문 |
| 2′ | /resume "어두운 골목 무서워요" | discover→extract→discover | ⏸ 택배보안 역질문 | 발굴카드(야간안전) |
| 2″ | /resume "택배도 챙겨주세요" | …→extract→prioritize | ⏸ 우선순위 편집 | 발굴카드(택배보안) |
| 2‴ | /resume {order:[safety,budget,commute]} | prioritize→filter→…→ground_check→respond | — | TOP3 (A86/B78/C71), 1:6 배지 |
| 3 | "C 방음 어때요?" | ingest(ask_listing)→respond | — | "설명에 없어 지어내지 않음" |
| 4 | "입지 설명해줘" | ingest(ask_location)→location→respond | (선택 캐시 시 생략) | A·B 입지 해설 |
| 5 | "월세 5만 더 올리면?" | ingest(edit→rent inc5)→filter→…→respond | — | 9→14건, D신축 91점 신규 1위, 델타 |

> 이 표가 그대로 `tests/test_graph.py`의 시나리오 테스트 케이스가 된다(LLM 노드는 응답 모킹).

---

## 10. 함정·주의 (구현 시)

1. **interrupt 앞 부수효과 금지** — 재개 시 노드가 처음부터 재실행된다. DB write·카드 emit은 `interrupt` *이후*에.
2. **리듀서 없는 키는 교체** — `cards`만 누적 리듀서. `hard`/`ranked`는 노드가 매번 최종값을 반환하므로 교체로 충분.
3. **루프 종료 보장** — `discover↔extract` 루프는 `MAX_DISCOVER` + `asked_dimensions`로 무한루프 차단.
4. **재진입 vs 재개 판별** — 반드시 `get_state().next`로 확인. 잘못하면 interrupt 중인데 새 입력을 넣어 상태 꼬임.
5. **스트림 모드** — `["custom","updates"]` 동시 구독. `values`는 전체 상태라 트래픽 큼, 데모엔 부적합.
6. **thread_id = 세션** — 같은 세션은 같은 `thread_id`로만 호출해야 체크포인트가 이어진다.
```
