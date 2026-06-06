"""실제 Upstage Solar Provider (구현스펙 §1, §5~§7).

langchain-upstage / httpx 는 이 모듈에서만 import 한다(필요 시 지연 로딩).
설치·API 키 없이도 mock 경로는 동작하도록 클래스 import 시점에 SDK를 강제하지 않는다.

라이브 검증 결과(스모크 테스트, scripts/smoke_upstage.py):
  - solar-pro2 / solar-mini / solar-embedding-1-large(dim 4096) 가용 ✅
  - with_structured_output(dict) 는 스키마에 top-level "title" 필요 → prompts.py 반영 ✅
  - Upstage groundedness-check 전용 모델은 폐기됨 → LLM-as-Judge(solar-mini)로 대체 ✅
"""

from __future__ import annotations

import os

from app.data.seed import Listing
from app.prompts import (
    EXTRACT_SCHEMA,
    EXTRACT_SYSTEM,
    GROUNDEDNESS_SCHEMA,
    GROUNDEDNESS_SYSTEM,
    INTENT_SCHEMA,
    INTENT_SYSTEM,
    SCORE_SCHEMA,
    SCORE_SYSTEM,
)
from app.providers.base import Provider
from app.scoring import match_geo
from app.state import ConditionCard, MatchResult


class UpstageProvider(Provider):
    name = "upstage"

    def __init__(self, pro_model: str = "solar-pro2", mini_model: str = "solar-mini"):
        from langchain_upstage import ChatUpstage, UpstageEmbeddings  # lazy

        if not os.getenv("UPSTAGE_API_KEY"):
            raise RuntimeError("UPSTAGE_API_KEY 가 필요합니다 (ROOMPILOT_PROVIDER=mock 로 우회 가능).")
        self._llm_pro = ChatUpstage(model=pro_model, temperature=0.2)
        self._llm_mini = ChatUpstage(model=mini_model, temperature=0)
        self._emb = UpstageEmbeddings(model="solar-embedding-1-large")

    def classify_intent(self, text: str, stage: str) -> dict:
        out = self._llm_mini.with_structured_output(INTENT_SCHEMA).invoke(
            [{"role": "system", "content": INTENT_SYSTEM}, {"role": "user", "content": text}]
        )
        return {"intent": out.get("intent", "chitchat"), "edit": out.get("edit")}

    def extract(self, text, cards, asked_dimensions, hard):
        out = self._llm_pro.with_structured_output(EXTRACT_SCHEMA).invoke(
            [{"role": "system", "content": EXTRACT_SYSTEM}, {"role": "user", "content": text}]
        )
        new = [self._to_card(c, asked_dimensions) for c in out.get("cards", [])]
        updates = {}
        for c in new:
            if c.kind == "hard":
                updates.update(_card_to_hard(c, text))
        return new, updates

    def discover_question(self, category, desc, cards) -> str:
        prompt = (
            f"사용자의 생활 맥락에서 '{desc}'({category}) 차원을 공감+근거 형태로 한 문장 역질문해라. "
            "설문처럼 묻지 말고 자연스럽게."
        )
        return self._llm_pro.invoke([{"role": "user", "content": prompt}]).content

    def embed(self, text: str) -> list[float]:
        return self._emb.embed_query(text)

    def score_listing(self, listing, cards):
        soft = [c for c in cards if c.kind == "soft"]
        payload = {
            "desc": listing.desc,
            "cards": [{"id": c.id, "label": c.label, "category": c.category} for c in soft],
        }
        out = self._llm_pro.with_structured_output(SCORE_SCHEMA).invoke(
            [
                {"role": "system", "content": SCORE_SYSTEM},
                {"role": "user", "content": str(payload)},
            ]
        )
        breakdown = [
            MatchResult(card_id=b["card_id"], status=b["status"], evidence=b.get("evidence", ""))
            for b in out.get("breakdown", [])
        ]
        self._fill_geo(listing, soft, breakdown)
        return breakdown, out.get("tradeoff")

    def check_grounded(self, context: str, answer: str) -> str:
        # Upstage groundedness-check 전용 모델이 폐기되어 LLM-as-Judge로 판정(Practice09).
        # solar-mini는 이 판정에서 신뢰도가 낮아(스모크 확인) 플래그십 solar-pro2를 쓴다.
        if not answer:
            return "notSure"
        out = self._llm_pro.with_structured_output(GROUNDEDNESS_SCHEMA).invoke(
            [
                {"role": "system", "content": GROUNDEDNESS_SYSTEM},
                {"role": "user", "content": f"[context]\n{context}\n\n[answer]\n{answer}"},
            ]
        )
        return out.get("verdict", "notSure")

    def analyze_location(self, listing, cards, priority_order):
        # 입지 raw(geo/location) 를 카드 관점으로 번역. 데모는 시드 location 을 기반으로 LLM 보강.
        return {**listing.location, "dataSource": "seed"}

    def _to_card(self, c: dict, asked: list[str]) -> ConditionCard:
        source = c.get("source", "extracted")
        if asked and source != "said" and c.get("category") == (asked[-1] if asked else None):
            source = "discovered"
        return ConditionCard(
            id=f"c_{c['category']}",
            label=c["label"],
            category=c["category"],
            kind=c.get("kind", "soft"),
            source=source,
            reason=c.get("reason", ""),
        )

    def _fill_geo(self, listing: Listing, soft, breakdown) -> None:
        have = {m.card_id for m in breakdown}
        for c in soft:
            if c.category in ("transit", "commute") and c.id not in have:
                key = "station_walk_min" if c.category == "transit" else "campus_walk_min"
                wm = int(listing.geo.get(key, 99))
                breakdown.append(
                    MatchResult(card_id=c.id, status=match_geo(c.category, wm), evidence=f"도보 {wm}분")
                )


def _card_to_hard(card: ConditionCard, text: str) -> dict:
    import re

    if card.category == "area":
        return {"area": "부산대"}
    if card.category == "budget":
        out: dict = {}
        nums = re.findall(r"\d+", text)
        if len(nums) >= 2:
            out["deposit"], out["rent"] = int(nums[0]), int(nums[1])
        return out
    return {}
