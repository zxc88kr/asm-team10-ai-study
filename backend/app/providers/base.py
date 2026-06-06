"""Provider 인터페이스.

mock / upstage 두 구현이 동일 시그니처를 따른다. 노드는 이 추상 타입에만 의존한다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.data.seed import Listing
from app.state import ConditionCard, MatchResult


class Provider(ABC):
    name: str = "base"

    # --- Agent 1: 니즈 통역사 ---
    @abstractmethod
    def classify_intent(self, text: str, stage: str) -> dict:
        """{"intent": ..., "edit": {field, op, value} | None} (오케스트레이션 §2)."""

    @abstractmethod
    def extract(
        self,
        text: str,
        cards: list[ConditionCard],
        asked_dimensions: list[str],
        hard: dict,
    ) -> tuple[list[ConditionCard], dict]:
        """발화 → (신규 카드, 하드 제약 갱신). 근거 없는 카드 생성 금지(구현스펙 §5.1)."""

    @abstractmethod
    def discover_question(
        self, category: str, desc: str, cards: list[ConditionCard]
    ) -> str:
        """사각지대 1개에 대한 공감+근거형 역질문(구현스펙 §5.2)."""

    # --- Agent 2: 매물 큐레이터 ---
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """의미 임베딩(구현스펙 §6.2)."""

    @abstractmethod
    def score_listing(
        self, listing: Listing, cards: list[ConditionCard]
    ) -> tuple[list[MatchResult], str | None]:
        """카드별 충족도 판정(status/evidence) + 트레이드오프 문구(구현스펙 §6.3).

        설명에 없는 정보는 추론하지 않고 status=none, evidence="" (환각 금지).
        """

    @abstractmethod
    def check_grounded(self, context: str, answer: str) -> str:
        """'grounded' | 'notGrounded' | 'notSure' (구현스펙 §6.4)."""

    # --- Agent 3: 입지 해설사 ---
    @abstractmethod
    def analyze_location(
        self, listing: Listing, cards: list[ConditionCard], priority_order: list[str]
    ) -> dict:
        """입지 raw 데이터를 사용자 카드 관점으로 번역(구현스펙 §7)."""
