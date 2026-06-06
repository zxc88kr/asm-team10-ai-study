"""상태 스키마 + 리듀서 단위 테스트."""

from app.state import (
    ConditionCard,
    derived_count,
    differentiation_ratio,
    merge_cards,
    said_count,
)


def _card(label, source, category="x", kind="soft", weight=2):
    return ConditionCard(
        id=f"c_{label}", label=label, category=category, kind=kind,
        source=source, reason="r", weight=weight,
    )


def test_merge_cards_upsert_by_label():
    existing = [_card("심야 교통", "extracted")]
    merged = merge_cards(existing, [_card("심야 교통", "extracted", weight=3)])
    assert len(merged) == 1
    assert merged[0].weight == 3  # 재가중이 리듀서를 통과


def test_merge_cards_said_promotes_inference():
    existing = [_card("지역", "extracted")]
    merged = merge_cards(existing, [_card("지역", "said", kind="hard")])
    assert merged[0].source == "said"
    assert merged[0].kind == "hard"


def test_merge_cards_appends_new_label():
    merged = merge_cards([_card("a", "said")], [_card("b", "discovered")])
    assert {c.label for c in merged} == {"a", "b"}


def test_differentiation_ratio_counts():
    cards = [
        _card("지역", "said"), _card("예산", "said"),
        _card("심야", "extracted"), _card("주방", "extracted"), _card("통학", "extracted"),
        _card("안전", "discovered"), _card("택배", "discovered"), _card("채광", "discovered"),
    ]
    assert said_count(cards) == 2
    assert derived_count(cards) == 6
    assert differentiation_ratio(cards) == {"ratio": "1:3", "said": 2, "derived": 6}


def test_differentiation_ratio_no_said():
    cards = [_card("a", "extracted")]
    assert differentiation_ratio(cards)["ratio"] == "1:1"
