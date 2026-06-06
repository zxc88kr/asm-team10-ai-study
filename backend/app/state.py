"""공유 상태 스키마 + 카드 병합 리듀서.

구현스펙 §3 / 오케스트레이션 상세 §1 을 코드로 옮긴 것.
그래프 상태는 평탄화(`cards`/`hard`/`priority_order` 분리)하여 리듀서를 명확히 건다.
"""

from __future__ import annotations

from typing import Annotated, Literal

from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypedDict

CardSource = Literal["said", "extracted", "discovered"]  # 직접발화 / 추출 / 발굴
MatchStatus = Literal["full", "partial", "none"]
Kind = Literal["hard", "soft"]


def _camel(s: str) -> str:
    head, *tail = s.split("_")
    return head + "".join(w.capitalize() for w in tail)


class _CamelModel(BaseModel):
    """직렬화 시 camelCase 별칭(프론트엔드 `types.ts` 정합)."""

    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)


class ConditionCard(_CamelModel):
    id: str
    label: str  # "야간 안전 동선"
    category: str  # "safety" | "transit" | "budget" | "kitchen" ...
    kind: Kind  # 🟦하드 / 🟩소프트·🟧발굴
    weight: int = Field(default=2, ge=0, le=3)  # ★ 0~3 (우선순위)
    source: CardSource
    reason: str  # 근거 발화 인용 또는 (추론) 근거 — 환각 방지 핵심
    confidence: float = 1.0


class MatchResult(_CamelModel):
    card_id: str
    status: MatchStatus
    evidence: str = ""  # 매물 설명에서 인용한 근거 문장
    grounded: bool | None = None  # Groundedness Check 결과


class ScoredListing(_CamelModel):
    listing_id: str
    score: int
    excluded: bool = False
    breakdown: list[MatchResult] = Field(default_factory=list)
    penalty: int = 0
    tradeoff: str | None = None  # "안전 최상 ↔ 요리 환경 아쉬움"


def said_count(cards: list[ConditionCard]) -> int:
    return sum(c.source == "said" for c in cards)


def derived_count(cards: list[ConditionCard]) -> int:  # 추출 + 발굴
    return sum(c.source != "said" for c in cards)


def differentiation_ratio(cards: list[ConditionCard]) -> dict:
    """핵심 차별 지표. 스펙 메트릭 계약 {ratio:"1:6", said:2, derived:6} 에 맞춰
    사용자측(직접 발화)을 1로 정규화한다. said/derived 는 별도 필드로 그대로 노출."""
    said = said_count(cards)
    derived = derived_count(cards)
    ratio = f"1:{derived}" if said else f"0:{derived}"
    return {"ratio": ratio, "said": said, "derived": derived}


def merge_cards(
    existing: list[ConditionCard], new: list[ConditionCard]
) -> list[ConditionCard]:
    """label 기준 upsert 리듀서.

    같은 label 재등장 시 confidence·근거 갱신, 직접 발화(said)가 추론을 승격 덮어쓸 수
    있게(반대는 금지) 처리. 카드는 매 노드가 누적하므로 교체가 아니라 병합이 필요하다.
    """
    by_label: dict[str, ConditionCard] = {c.label: c for c in existing}
    for c in new:
        prev = by_label.get(c.label)
        if prev is None:
            by_label[c.label] = c
            continue
        if prev.source != "said" and c.source == "said":
            prev.source, prev.kind = "said", c.kind
        prev.confidence = max(prev.confidence, c.confidence)
        prev.weight = c.weight  # prioritize 재가중이 리듀서를 통과하도록 반영
        if c.reason:
            prev.reason = c.reason
    return list(by_label.values())


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    cards: Annotated[list[ConditionCard], merge_cards]  # ★ 리듀서로 누적
    hard: dict  # {deposit, rent, area, mgmt_fee_max, commute_max}
    priority_order: list[str]
    candidates: list[str]
    candidate_count: int
    ranked: list[ScoredListing]
    location_analysis: dict
    selected_listing: str | None  # location_node 가 이번 턴에 해설한 매물
    asked_dimensions: list[str]
    stage: str  # "needs" | "listings" | "location" | "done"
    intent: str  # ingest가 채움
    prev_candidate_count: int
    prev_top_id: str | None


def init_state() -> AgentState:
    return {
        "messages": [],
        "cards": [],
        "hard": {},
        "priority_order": [],
        "candidates": [],
        "candidate_count": 0,
        "ranked": [],
        "location_analysis": {},
        "asked_dimensions": [],
        "stage": "needs",
        "intent": "",
        "prev_candidate_count": 0,
        "prev_top_id": None,
    }
