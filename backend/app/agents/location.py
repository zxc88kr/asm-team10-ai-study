"""Agent 3 「입지 해설사」 — `location_node`. 구현스펙 §7 / 오케스트레이션 §5.

상위 후보만 입지 분석(나머지는 캐시). 입지 raw 데이터를 사용자 카드 관점으로 번역.
"""

from __future__ import annotations

from app.data.seed import get_listing
from app.events import emit
from app.providers import get_provider
from app.state import AgentState


def location_node(state: AgentState) -> dict:
    ranked = state.get("ranked", [])
    if not ranked:
        return {}
    selected = _current_selection(state, ranked)

    cached = dict(state.get("location_analysis", {}))
    if selected not in cached:  # 상위 후보만 실시간, 나머지는 캐시 재사용
        analysis = get_provider().analyze_location(
            get_listing(selected), state.get("cards", []), state.get("priority_order", [])
        )
        cached[selected] = analysis
        emit({"type": "location", "listingId": selected, "analysis": analysis})
    return {"location_analysis": cached}


def _current_selection(state: AgentState, ranked) -> str:
    """직전 사용자 발화에서 선택된 매물, 없으면 TOP-1.

    참고: 선택이 없으면 interrupt(select_listing)로 물을 수도 있으나(오케스트레이션 §5),
    데모 결정성을 위해 TOP-1을 기본 선택한다.
    """
    messages = state.get("messages", [])
    if messages:
        text = messages[-1].content
        for sl in ranked:
            if sl.listing_id in text or get_listing(sl.listing_id).name in text:
                return sl.listing_id
    return ranked[0].listing_id
