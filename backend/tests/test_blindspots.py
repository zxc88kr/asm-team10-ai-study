"""사각지대 선택 로직 테스트."""

from app.blindspots import pick_blind_spot
from app.state import ConditionCard


def _card(category):
    return ConditionCard(
        id=f"c_{category}", label=category, category=category, kind="soft",
        source="extracted", reason="r",
    )


def test_pick_blind_spot_priority_order():
    state = {"cards": [], "asked_dimensions": []}
    assert pick_blind_spot(state)[0] == "safety"  # 우선순위 1순위


def test_pick_blind_spot_skips_carded():
    state = {"cards": [_card("safety")], "asked_dimensions": []}
    assert pick_blind_spot(state)[0] == "security"


def test_pick_blind_spot_skips_asked():
    state = {"cards": [], "asked_dimensions": ["safety", "security"]}
    assert pick_blind_spot(state)[0] == "light"


def test_pick_blind_spot_exhausted():
    state = {
        "cards": [_card(c) for c in ("safety", "security", "light", "noise", "kitchen")],
        "asked_dimensions": [],
    }
    assert pick_blind_spot(state) is None
