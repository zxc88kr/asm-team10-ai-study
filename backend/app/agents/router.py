"""진입 라우터 `ingest` — 의도 분류 + 조건 편집(루프백 시발점). 오케스트레이션 §2."""

from __future__ import annotations

from app.providers import get_provider
from app.state import AgentState


def ingest_node(state: AgentState) -> dict:
    last = state["messages"][-1].content
    out = get_provider().classify_intent(last, state.get("stage", "needs"))
    update: dict = {"intent": out["intent"]}
    if out["intent"] == "edit_condition" and out.get("edit"):
        # 루프백: 재추천 전에 직전 결과를 stash(델타 계산용)
        ranked = state.get("ranked") or []
        update["prev_candidate_count"] = state.get("candidate_count", 0)
        update["prev_top_id"] = ranked[0].listing_id if ranked else None
        update["hard"] = apply_condition_edit(dict(state.get("hard", {})), out["edit"])
    return update


def route_from_ingest(state: AgentState) -> str:
    if state.get("stage", "needs") == "needs":
        return "extract"  # 아직 니즈 수집 중
    intent = state.get("intent", "")
    if intent == "edit_condition":
        return "filter"  # 루프백: 재추천
    if intent in ("select_listing", "ask_location"):
        return "location"
    if intent in ("ask_listing", "chitchat"):
        return "respond"
    return "extract"  # provide_info 등


def apply_condition_edit(hard: dict, edit: dict) -> dict:
    field, op, value = edit["field"], edit["op"], edit.get("value", 0)
    if field == "area":
        hard[field] = value
    elif op == "set":
        hard[field] = value
    elif op == "inc":
        hard[field] = hard.get(field, 0) + value
    elif op == "dec":
        hard[field] = hard.get(field, 0) - value
    return hard  # 예: 월세 50→55  ("월세 +5만" 루프백)
