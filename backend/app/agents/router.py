"""진입 라우터 `ingest` — 의도 분류 + 조건 편집(루프백 시발점). 오케스트레이션 §2."""

from __future__ import annotations

from app.providers import get_provider
from app.state import AgentState

_EDIT_FIELDS = {"rent", "deposit", "commute_max", "area", "mgmt_fee_max"}


def ingest_node(state: AgentState) -> dict:
    last = state["messages"][-1].content
    stage = state.get("stage", "needs")
    out = get_provider().classify_intent(last, stage)
    # 니즈 단계에선 분류 결과와 무관하게 정보 수집으로 고정(provider 간 동작 일치).
    intent = "provide_info" if stage == "needs" else out.get("intent", "chitchat")
    update: dict = {"intent": intent}
    edited = _maybe_apply_edit(state, intent, out.get("edit"))
    if edited is not None:
        update.update(edited)
    else:
        update["intent"] = "chitchat" if intent == "edit_condition" else intent
    return update


def _maybe_apply_edit(state: AgentState, intent: str, edit: object) -> dict | None:
    """유효한 edit면 hard 갱신 + 델타용 stash 반환, 아니면 None(편집 무시)."""
    if intent != "edit_condition" or not isinstance(edit, dict):
        return None
    field = edit.get("field")
    if field not in _EDIT_FIELDS:
        return None
    ranked = state.get("ranked") or []
    return {
        "prev_candidate_count": state.get("candidate_count", 0),
        "prev_top_id": ranked[0].listing_id if ranked else None,
        "hard": apply_condition_edit(dict(state.get("hard", {})), edit),
    }


def route_from_ingest(state: AgentState) -> str:
    if state.get("stage", "needs") == "needs":
        return "extract"  # 아직 니즈 수집 중
    intent = state.get("intent", "")
    if intent == "edit_condition":
        return "filter"  # 루프백: 재추천
    if intent in ("select_listing", "ask_location"):
        return "location"
    # 니즈 단계 이후엔 분류가 불확실해도 재추출하지 않고 응답으로 안전하게 흘린다
    # (실 LLM 오분류로 prioritize 재진입하는 문제 방지). 니즈 단계는 위에서 이미 extract 처리.
    return "respond"


def apply_condition_edit(hard: dict, edit: dict) -> dict:
    field, op, value = edit["field"], edit.get("op", "set"), edit.get("value", 0)
    if field == "area":
        hard[field] = value
    elif op == "set":
        hard[field] = value
    elif op == "inc":
        hard[field] = hard.get(field, 0) + value
    elif op == "dec":
        hard[field] = hard.get(field, 0) - value
    return hard  # 예: 월세 50→55  ("월세 +5만" 루프백)
