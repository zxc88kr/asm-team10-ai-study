"""Agent 1 「니즈 통역사」 — extract / discover / prioritize. 오케스트레이션 §3."""

from __future__ import annotations

from typing import Any

from langgraph.types import interrupt

from app.blindspots import pick_blind_spot
from app.events import emit
from app.providers import get_provider
from app.scoring import priority_weights
from app.state import AgentState, ConditionCard, differentiation_ratio

MAX_DISCOVER = 3  # 설문화 방지: 발굴 역질문 최대 횟수


def extract_node(state: AgentState) -> dict:
    last = state["messages"][-1].content
    provider = get_provider()
    new_cards, hard_updates = provider.extract(
        last, state.get("cards", []), state.get("asked_dimensions", []), state.get("hard", {})
    )
    for c in new_cards:  # 카드 즉시 push (실시간 채움)
        emit({"type": "card", "card": c.model_dump(by_alias=True)})

    hard = dict(state.get("hard", {}))
    hard.update(hard_updates)

    ratio = differentiation_ratio(state.get("cards", []) + new_cards)
    emit({"type": "metric", **ratio})  # FE 상단 1:6 배지
    return {"cards": new_cards, "hard": hard}


def route_after_extract(state: AgentState) -> str:
    cards = state.get("cards", [])
    has_soft = any(c.kind == "soft" for c in cards)
    if not has_soft:
        return "respond"  # 하드 카드만 → "하루 일과 들려주세요" 유도 후 턴 종료
    if len(state.get("asked_dimensions", [])) < MAX_DISCOVER and pick_blind_spot(state):
        return "discover"
    return "prioritize"  # 사각지대 소진 → 우선순위 편집


def discover_node(state: AgentState) -> dict:
    blind = pick_blind_spot(state)
    assert blind is not None, "route_after_extract가 사각지대 존재를 보장"
    cat, desc = blind
    question = get_provider().discover_question(cat, desc, state.get("cards", []))

    # ⏸ 여기서 멈춘다. interrupt 앞에 부수효과를 두지 않는다(재개 시 재실행됨).
    raw = interrupt({"type": "discover_question", "category": cat, "text": question})

    # resume 후: 사용자의 답을 메시지에 싣고 asked에 기록 → extract가 카드화.
    # HTTP /resume 가 비문자열을 보내도 안전하게 문자열로 정규화한다.
    answer = _resume_text(raw)
    return {
        "messages": [{"role": "user", "content": answer}],
        "asked_dimensions": state.get("asked_dimensions", []) + [cat],
    }


def _resume_text(raw: Any) -> str:
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return str(raw.get("text", ""))
    return str(raw)


def prioritize_node(state: AgentState) -> dict:
    soft_cats = sorted({c.category for c in state.get("cards", []) if c.kind == "soft"})
    order = interrupt({"type": "edit_priority", "categories": soft_cats})  # ⏸ FE 편집 UI

    # resume: 사용자가 정렬한 순서로 가중치 부여 (1순위=3 …). 페이로드 형태에 방어적.
    chosen = _coerce_order(order, soft_cats)
    weights = priority_weights(chosen)
    cards = [
        _reweight(c, weights.get(c.category, c.weight)) for c in state.get("cards", [])
    ]
    return {"priority_order": chosen, "cards": cards, "stage": "listings"}


def _coerce_order(order: Any, soft_cats: list[str]) -> list[str]:
    """resume 페이로드를 우선순위 리스트로 정규화. {"order":[...]} / [...] / 그 외 → 기본값."""
    if isinstance(order, dict):
        return order.get("order") or soft_cats
    if isinstance(order, list):
        return order
    return soft_cats


def _reweight(card: ConditionCard, weight: int) -> ConditionCard:
    return card.model_copy(update={"weight": weight})
