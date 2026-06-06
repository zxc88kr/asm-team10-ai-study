"""순수 점수 로직 — 카드 ↔ 매물 매칭 규칙과 가중 점수 계산.

구현스펙 §6.3. LLM 판정(status/evidence)은 provider가, 가중 합산은 이 모듈이 담당한다(역할 분리).
규칙 기반 매칭은 mock provider와 단위 테스트가 공유한다.
"""

from __future__ import annotations

from app.state import ConditionCard, MatchResult, MatchStatus

STATUS_VAL: dict[MatchStatus, float] = {"full": 1.0, "partial": 0.5, "none": 0.0}

# 매물 설명(desc) 키워드 기반 매칭 규칙. neg가 하나라도 있으면 none, 아니면 pos 있으면 full.
# (commute/transit은 desc가 아니라 geo 수치로 판정 → match_geo 사용)
DESC_RULES: dict[str, dict[str, list[str]]] = {
    "safety": {"pos": ["가로등", "편의점", "대로변", "밝"], "neg": ["가로등 적", "어두운", "우범"]},
    "security": {"pos": ["도어락", "무인택배함", "공동현관", "경비"], "neg": []},
    "kitchen": {"pos": ["분리형"], "neg": ["개방형"]},
    "light": {"pos": ["남향", "채광 좋", "환기 잘"], "neg": ["채광 다소", "채광은 다소", "채광 제한"]},
}

# weight 부여 규칙: 우선순위 1순위=3, 2순위=2, 3순위=1, 그 외 soft 카드=기본값 유지.
DEFAULT_SOFT_WEIGHT = 2
PRIORITY_PENALTY = 8  # 1순위 카드가 full이 아니면 감점


def match_desc(category: str, desc: str) -> MatchStatus:
    rule = DESC_RULES.get(category)
    if rule is None:
        return "none"
    if any(k in desc for k in rule["neg"]):
        return "none"
    if any(k in desc for k in rule["pos"]):
        return "full"
    return "none"


def match_geo(category: str, walk_min: int) -> MatchStatus:
    """transit(역까지)·commute(캠퍼스까지) 거리 기반 판정."""
    if walk_min <= 7:
        return "full"
    if walk_min <= 15:
        return "partial"
    return "none"


def assign_weights(
    cards: list[ConditionCard], priority_order: list[str]
) -> dict[str, int]:
    """카테고리별 가중치. 우선순위 순서대로 3,2,1 부여, 나머지는 카드 weight 유지."""
    weights: dict[str, int] = {}
    for idx, cat in enumerate(priority_order):
        weights[cat] = max(3 - idx, 1)
    for c in cards:
        weights.setdefault(c.category, c.weight or DEFAULT_SOFT_WEIGHT)
    return weights


def compute_score(
    cards: list[ConditionCard],
    breakdown: list[MatchResult],
    priority_order: list[str],
) -> tuple[int, int]:
    """가중 점수와 penalty를 반환.

    score = Σ(weight × statusVal) / Σweight × 100 − penalty
    1순위 카드가 full이 아니면 penalty 가산.
    """
    soft = [c for c in cards if c.kind == "soft"]
    weights = assign_weights(soft, priority_order)
    by_card = {m.card_id: m for m in breakdown}

    total_w = sum(weights.get(c.category, DEFAULT_SOFT_WEIGHT) for c in soft)
    if total_w == 0:
        return 0, 0
    acc = 0.0
    for c in soft:
        w = weights.get(c.category, DEFAULT_SOFT_WEIGHT)
        m = by_card.get(c.id)
        if m is not None:
            acc += w * STATUS_VAL[m.status]
    base = round(acc / total_w * 100)

    penalty = 0
    if priority_order:
        top_cat = priority_order[0]
        top_cards = [c for c in soft if c.category == top_cat]
        for c in top_cards:
            m = by_card.get(c.id)
            if m is None or m.status != "full":
                penalty = PRIORITY_PENALTY
                break
    return max(base - penalty, 0), penalty
