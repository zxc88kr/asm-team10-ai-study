from __future__ import annotations

import json
import operator
from copy import deepcopy
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph

from .listing_curator import ListingCurator
from .rule_extractor import apply_rule_extraction
from .schema import ConditionState, create_empty_conditions, update_missing_and_question
from .solar_client import SolarClientError, call_upstage_json, get_solar_api_key


SYSTEM_PROMPT = """
너는 자취방 조건을 정리하는 부동산 조건 추출 agent다.
반드시 JSON 객체만 반환한다.
최상위 키는 반드시 hard_conditions, soft_conditions, missing_required_conditions, next_question, is_complete, next_action 만 사용한다.
current_state, user_message, required_output_shape 같은 wrapper 키를 반환하지 않는다.

분류 규칙:
- hard_conditions.location_transport: 위치/교통 조건. 지역, 역, 출퇴근 시간, 도보/지하철/버스 조건.
- hard_conditions.monthly_rent: 월세 조건. 관리비 포함 여부도 여기에 둔다.
- soft_conditions.convenience_facilities: 편의 시설. 편의점, 마트, 병원, 약국, 카페, 세탁소 등.
- soft_conditions.pests: 벌레 여부. 벌레, 바퀴벌레, 해충 회피.
- soft_conditions.default_options: 기본 옵션. 에어컨, 냉장고, 세탁기, 침대 등.
- soft_conditions.basement: 반지하 여부.
- soft_conditions.mold: 곰팡이, 습기, 결로.

기존 state를 유지하면서 새 유저 메시지에 나온 조건만 병합한다.
모르는 값은 null 또는 빈 배열로 둔다.
하드 조건 위치/교통과 월세가 비어 있으면 missing_required_conditions에 넣는다.
next_question에는 다음에 물어볼 한 문장만 넣는다.

[next_action 판단 규칙 — 에이전트가 직접 결정]
next_action은 아래 세 값 중 하나로 설정한다:

"ask_required_conditions"
  - 위치/교통 또는 월세 정보가 아직 없을 때

"recommend_listings"
  - 사용자가 명시적으로 추천·검색을 요청할 때 ("찾아줘", "추천해줘", "보여줘", "됐어")
  - 사용자가 조건을 다 말했다는 신호를 줄 때 ("없어", "더 없어", "그게 다야", "이 정도면 돼")
  - 소프트 조건을 1개 이상 받은 상태에서 사용자 발화에 새 조건이 없을 때
  - is_complete=true, next_question에는 추천을 시작한다는 짧은 안내 문구 작성

"ask_soft_conditions"
  - 소프트 조건을 아직 하나도 받지 못했고 사용자가 계속 조건을 말하는 중일 때
  - is_complete=false

규칙 기반으로 100% 판단할 수 없는 경우(뉘앙스·의도 불명확)는 에이전트가 문맥을 읽고 직접 결정한다.
""".strip()


class AgentState(TypedDict):
    messages: Annotated[list[dict[str, str]], operator.add]
    conditions: ConditionState
    use_solar: bool
    api_key: str | None


def _deep_merge(base: Any, new: Any) -> Any:
    if isinstance(base, dict) and isinstance(new, dict):
        merged = deepcopy(base)
        for key, value in new.items():
            if key in merged:
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged

    if isinstance(base, list) and isinstance(new, list):
        result = list(base)
        for item in new:
            if item not in result:
                result.append(item)
        return result

    if new is None:
        return deepcopy(base)
    return deepcopy(new)


def _handle_with_solar(
    conditions: ConditionState,
    user_message: str,
    api_key: str | None,
    history: list[dict[str, str]],
) -> ConditionState:
    current_user_content = json.dumps(
        {
            "current_state": conditions,
            "user_message": user_message,
            "required_output_shape": create_empty_conditions(),
        },
        ensure_ascii=False,
    )
    # 대화 히스토리를 포함해 LLM에 전달 (system + 이전 turns + 현재 user)
    llm_messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[:-1]:  # 마지막 user 메시지는 구조화된 형태로 교체
        role = msg["role"] if msg["role"] in ("user", "assistant") else "user"
        llm_messages.append({"role": role, "content": msg["content"]})
    llm_messages.append({"role": "user", "content": current_user_content})

    prompt = "\n\n".join([SYSTEM_PROMPT, current_user_content])
    solar_state = call_upstage_json(prompt=prompt, messages=llm_messages, api_key=api_key)
    next_state = _deep_merge(conditions, solar_state)
    next_state = apply_rule_extraction(next_state, user_message)
    next_state["agent_mode"] = "solar"
    return update_missing_and_question(next_state, trust_llm_action=True)


# ── 노드 ────────────────────────────────────────────────────────────────────

def extract_conditions_node(state: AgentState) -> dict[str, Any]:
    """Solar LLM 또는 규칙 추출기로 조건을 추출하고 next_action을 결정한다."""
    user_message = state["messages"][-1]["content"]
    conditions = deepcopy(state["conditions"])
    use_solar = state.get("use_solar", True)
    api_key = state.get("api_key")

    if use_solar and (api_key or get_solar_api_key()):
        try:
            conditions = _handle_with_solar(conditions, user_message, api_key, state["messages"])
        except SolarClientError:
            conditions = apply_rule_extraction(conditions, user_message)
            conditions["agent_mode"] = "rule_fallback"
    else:
        conditions = apply_rule_extraction(conditions, user_message)
        conditions["agent_mode"] = "rule"

    return {"conditions": conditions}


def recommend_node(state: AgentState) -> dict[str, Any]:
    """ListingCurator를 실행해 top_properties를 conditions에 추가한다."""
    conditions = state["conditions"]
    use_solar = state.get("use_solar", True)
    api_key = state.get("api_key")

    try:
        curator = ListingCurator(use_solar=use_solar, api_key=api_key)
        result = curator.recommend(conditions=conditions, top_n=5)
        updated = {**deepcopy(conditions), "top_properties": result["top_properties"]}
    except Exception:
        updated = deepcopy(conditions)

    return {"conditions": updated}


# ── 라우터 ───────────────────────────────────────────────────────────────────

def route_action(state: AgentState) -> str:
    """next_action 값에 따라 다음 노드를 결정한다."""
    return state["conditions"].get("next_action", "ask_required_conditions")


# ── 그래프 조립 ──────────────────────────────────────────────────────────────

def build_graph() -> Any:
    graph: StateGraph = StateGraph(AgentState)

    graph.add_node("extract_conditions", extract_conditions_node)
    graph.add_node("recommend", recommend_node)

    graph.set_entry_point("extract_conditions")

    graph.add_conditional_edges(
        "extract_conditions",
        route_action,
        {
            "ask_required_conditions": END,
            "ask_soft_conditions": END,
            "recommend_listings": "recommend",
        },
    )

    graph.add_edge("recommend", END)

    return graph.compile()


agent_graph = build_graph()
