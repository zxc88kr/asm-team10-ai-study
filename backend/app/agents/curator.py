"""Agent 2 「매물 큐레이터」 — filter / embed_rank / score / ground_check + respond.

구현스펙 §6 / 오케스트레이션 §4. 하이브리드 매칭: 메타데이터 필터 → 임베딩 압축 → LLM 점수화 → 환각 게이트.
"""

from __future__ import annotations

import math

from app.data.seed import Listing, get_listing, load_listings
from app.events import emit
from app.providers import get_provider
from app.scoring import compute_score
from app.state import AgentState, ScoredListing

EMBED_TOP_K = 6  # 임베딩 후보 압축 상한


def filter_node(state: AgentState) -> dict:
    """하드 제약 압축(순수 함수, LLM 미사용). 시나리오 '42→9건'."""
    hard = state.get("hard", {})
    candidates = [L.id for L in load_listings() if _passes_hard(L, hard)]
    return {"candidates": candidates, "candidate_count": len(candidates)}


def embed_rank_node(state: AgentState) -> dict:
    """소프트 카드 묶음 ↔ 매물 desc 의미 유사도로 상위 K 압축(비용 절감)."""
    provider = get_provider()
    soft = [c for c in state.get("cards", []) if c.kind == "soft"]
    query = " / ".join(f"{c.label}: {c.reason}" for c in soft) or "원룸"
    qv = provider.embed(query)
    scored: list[tuple[str, float]] = []
    for lid in state.get("candidates", []):
        listing = get_listing(lid)
        dv = listing.embedding or provider.embed(listing.desc)
        scored.append((lid, _cosine(qv, dv)))
    scored.sort(key=lambda x: -x[1])
    return {"candidates": [lid for lid, _ in scored[:EMBED_TOP_K]]}


def score_node(state: AgentState) -> dict:
    """LLM 가중 점수화 + 근거 인용. 설명에 없으면 status=none(환각 금지)."""
    provider = get_provider()
    cards = state.get("cards", [])
    priority = state.get("priority_order", [])
    ranked: list[ScoredListing] = []
    for lid in state.get("candidates", []):
        breakdown, tradeoff = provider.score_listing(get_listing(lid), cards)
        score, penalty = compute_score(cards, breakdown, priority)
        ranked.append(
            ScoredListing(
                listing_id=lid, score=score, penalty=penalty,
                breakdown=breakdown, tradeoff=tradeoff,
            )
        )
    ranked.sort(key=lambda s: -s.score)
    emit({"type": "ranked", "ranked": [r.model_dump(by_alias=True) for r in ranked[:3]]})
    return {"ranked": ranked[:3]}


def ground_check_node(state: AgentState) -> dict:
    """환각 검증 게이트: 미근거 evidence 강등 후 점수 재계산·재정렬(구현스펙 §6.4)."""
    provider = get_provider()
    cards = state.get("cards", [])
    priority = state.get("priority_order", [])
    ranked = list(state.get("ranked", []))
    for sl in ranked:
        context = _grounding_context(get_listing(sl.listing_id))
        for m in sl.breakdown:
            if m.evidence:
                m.grounded = provider.check_grounded(context, m.evidence) == "grounded"
                if not m.grounded:  # 근거 미확인 → 강등
                    m.status, m.evidence = "none", ""
        sl.score, sl.penalty = compute_score(cards, sl.breakdown, priority)
    ranked.sort(key=lambda s: -s.score)
    emit({"type": "ranked", "grounded": True,
          "ranked": [r.model_dump(by_alias=True) for r in ranked]})
    return {"ranked": ranked}


def _grounding_context(listing: Listing) -> str:
    """근거 검증용 컨텍스트 = 설명 + 입지(geo) 사실.

    transit/commute는 desc가 아니라 geo에서 나온 사실이므로, desc만으로 검증하면
    오탈락한다. 입지 사실을 컨텍스트에 포함해 정상 근거로 인정한다.
    """
    g = listing.geo
    extra = (
        f" {g.get('subway', '')} 도보 {g.get('station_walk_min', '')}분"
        f" 캠퍼스 도보 {g.get('campus_walk_min', '')}분"
    )
    return listing.desc + extra


def _passes_hard(listing: Listing, hard: dict) -> bool:
    if not listing.area_matches(hard.get("area")):
        return False
    if "deposit" in hard and listing.deposit > hard["deposit"]:
        return False
    if "rent" in hard and listing.rent > hard["rent"]:
        return False
    if "mgmt_fee_max" in hard and listing.mgmt_fee > hard["mgmt_fee_max"]:
        return False
    return True


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
