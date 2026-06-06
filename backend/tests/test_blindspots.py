"""사각지대 선택 로직 테스트."""

from app.blindspots import pick_blind_spot
from app.state import AgentState, ConditionCard


def _card(category: str) -> ConditionCard:
    return ConditionCard(
        id=f"c_{category}", label=category, category=category, kind="soft",
        source="extracted", reason="r",
    )


def _first(state: AgentState) -> str:
    result = pick_blind_spot(state)
    assert result is not None
    return result[0]


def test_pick_blind_spot_priority_order():
    state: AgentState = {"cards": [], "asked_dimensions": []}
    assert _first(state) == "safety"  # 우선순위 1순위


def test_pick_blind_spot_skips_carded():
    state: AgentState = {"cards": [_card("safety")], "asked_dimensions": []}
    assert _first(state) == "security"


def test_pick_blind_spot_skips_asked():
    state: AgentState = {"cards": [], "asked_dimensions": ["safety", "security"]}
    assert _first(state) == "light"


def test_pick_blind_spot_exhausted():
    state: AgentState = {
        "cards": [_card(c) for c in ("safety", "security", "light", "noise", "kitchen")],
        "asked_dimensions": [],
    }
    assert pick_blind_spot(state) is None
