"""발굴 엔진 C — 사각지대 체크리스트.

구현스펙 §5.2. 아직 안 채워진 차원에서 '가장 중요한 1개만' 골라 역질문(설문화 방지).
"""

from __future__ import annotations

from app.state import AgentState

# (category, 사람이 읽는 설명) — 우선순위 순서대로 둔다.
# 'noise(방음)'는 카드화 대상이 아니라 '설명에 없으면 지어내지 않는다'는 환각 데모 주제이므로
# 발굴 차원에서 제외한다(점수화 가능한 category 만 둔다).
BLIND_SPOT_CHECKLIST: list[tuple[str, str]] = [
    ("safety", "야간 단독 귀가 동선 안전"),
    ("security", "택배·공동현관 보안"),
    ("light", "채광·환기·습기(곰팡이)"),
    ("kitchen", "주방 분리/환기"),
]


def pick_blind_spot(state: AgentState) -> tuple[str, str] | None:
    """미충족 차원 중 우선순위 1순위 1개. 카드로 채워졌거나 이미 물은 차원은 제외."""
    have = {c.category for c in state.get("cards", [])}
    asked = set(state.get("asked_dimensions", []))
    for cat, desc in BLIND_SPOT_CHECKLIST:
        if cat not in have and cat not in asked:
            return cat, desc
    return None
