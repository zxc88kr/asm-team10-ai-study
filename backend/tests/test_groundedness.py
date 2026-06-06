"""환각 검증 게이트(ground_check_node)가 실제로 근거 미달 카드를 강등하는지 검증.

구현스펙 §6.4 / §9 4계층 방어의 3계층. 평가(Groundedness) 레이어가 no-op이 아님을 증명.
"""

from app.agents.curator import ground_check_node
from app.providers import set_provider
from app.providers.mock import MockProvider
from app.state import AgentState, ConditionCard, MatchResult, ScoredListing


class _UngroundedProvider(MockProvider):
    """모든 근거를 notGrounded로 판정하는 평가자(강등 경로 강제)."""

    def check_grounded(self, context: str, answer: str) -> str:
        return "notGrounded"


def _safety_card() -> ConditionCard:
    return ConditionCard(
        id="c_safety", label="야간 안전 동선", category="safety",
        kind="soft", source="discovered", reason="(추론)", weight=3,
    )


def test_ground_check_demotes_ungrounded_evidence():
    set_provider(_UngroundedProvider())
    try:
        card = _safety_card()
        ranked = [
            ScoredListing(
                listing_id="A", score=100, penalty=0,
                breakdown=[MatchResult(card_id="c_safety", status="full", evidence="실제로는 없는 근거")],
            )
        ]
        state: AgentState = {"ranked": ranked, "cards": [card], "priority_order": ["safety"]}
        out = ground_check_node(state)
        result = out["ranked"][0].breakdown[0]
        assert result.grounded is False  # 근거 미확인
        assert result.status == "none"  # 강등됨
        assert result.evidence == ""
        assert out["ranked"][0].score < 100  # 점수 재계산으로 하락
    finally:
        set_provider(None)


def test_ground_check_keeps_grounded_evidence():
    set_provider(MockProvider())  # desc 인용 근거는 grounded로 통과
    try:
        card = _safety_card()
        # A빌라 desc 에 실재하는 문장을 근거로
        ranked = [
            ScoredListing(
                listing_id="A", score=90, penalty=0,
                breakdown=[MatchResult(card_id="c_safety", status="full", evidence="골목 초입 편의점·가로등 밝은 편")],
            )
        ]
        state: AgentState = {"ranked": ranked, "cards": [card], "priority_order": ["safety"]}
        out = ground_check_node(state)
        result = out["ranked"][0].breakdown[0]
        assert result.grounded is True
        assert result.status == "full"  # 유지
    finally:
        set_provider(None)
