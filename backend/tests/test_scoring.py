"""점수 로직 단위 테스트."""

from app.scoring import (
    assign_weights,
    compute_score,
    match_desc,
    match_geo,
)
from app.state import ConditionCard, MatchResult


def _soft(cid, category, weight=2):
    return ConditionCard(
        id=cid, label=cid, category=category, kind="soft", source="extracted", reason="r", weight=weight
    )


def test_match_desc_positive_negative():
    assert match_desc("kitchen", "주방 분리형, 인덕션") == "full"
    assert match_desc("kitchen", "개방형 주방") == "none"  # 부정 키워드 우선
    assert match_desc("light", "채광은 다소 제한적") == "none"
    assert match_desc("safety", "골목 초입 편의점·가로등 밝은 편") == "full"
    assert match_desc("safety", "일부 구간 가로등 적은 골목") == "none"


def test_match_geo_thresholds():
    assert match_geo("transit", 5) == "full"
    assert match_geo("transit", 12) == "partial"
    assert match_geo("transit", 20) == "none"


def test_assign_weights_priority_order():
    cards = [_soft("c_safety", "safety"), _soft("c_commute", "commute"), _soft("c_kitchen", "kitchen")]
    weights = assign_weights(cards, ["safety", "budget", "commute"])
    assert weights["safety"] == 3
    assert weights["commute"] == 1
    assert weights["kitchen"] == 2  # 우선순위 밖은 기본값 유지


def test_compute_score_weighted_with_penalty():
    cards = [_soft("c_safety", "safety"), _soft("c_kitchen", "kitchen")]
    # 1순위(safety) 미충족 → penalty 적용
    breakdown = [
        MatchResult(card_id="c_safety", status="none"),
        MatchResult(card_id="c_kitchen", status="full"),
    ]
    score, penalty = compute_score(cards, breakdown, ["safety", "budget", "commute"])
    assert penalty == 8
    # safety(w3)=0, kitchen(w2)=1 → 2/5*100=40, -8 → 32
    assert score == 32


def test_compute_score_full_no_penalty():
    cards = [_soft("c_safety", "safety")]
    breakdown = [MatchResult(card_id="c_safety", status="full")]
    score, penalty = compute_score(cards, breakdown, ["safety"])
    assert (score, penalty) == (100, 0)
