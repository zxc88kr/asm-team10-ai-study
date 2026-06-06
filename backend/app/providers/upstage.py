"""실제 Upstage Solar Provider (구현스펙 §1, §5~§7).

langchain-upstage 는 이 모듈에서만 import 한다(필요 시 지연 로딩).
설치·API 키 없이도 mock 경로는 동작하도록 클래스 import 시점에 SDK를 강제하지 않는다.

라이브 검증 결과(스모크 테스트, scripts/smoke_upstage.py):
  - solar-pro2 / solar-mini / solar-embedding-1-large(dim 4096) 가용 ✅
  - with_structured_output(dict) 는 스키마에 top-level "title" 필요 → prompts.py 반영 ✅
  - Upstage groundedness-check 전용 모델은 폐기됨 → LLM-as-Judge(solar-pro2)로 대체 ✅

실 LLM 방어(리뷰 반영): 구조화 출력 None/형식이탈, enum 이탈 값, list 형 content 를 모두 정규화.
"""

from __future__ import annotations

import os
from typing import Any

from app.data.seed import Listing
from app.parsing import message_text, won_after
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

VALID_CATEGORIES = {"area", "budget", "safety", "transit", "commute", "kitchen", "light", "security"}
VALID_STATUS = {"full", "partial", "none"}
VALID_VERDICT = {"grounded", "notGrounded", "notSure"}


def _as_dict(out: Any) -> dict:
    """구조화 출력이 None/비dict 로 와도 안전하게 dict 로 정규화."""
    return out if isinstance(out, dict) else {}


class UpstageProvider(Provider):
    name = "upstage"

    def __init__(self, pro_model: str = "solar-pro2", mini_model: str = "solar-mini"):
        from langchain_upstage import ChatUpstage, UpstageEmbeddings  # lazy

        if not os.getenv("UPSTAGE_API_KEY"):
            raise RuntimeError("UPSTAGE_API_KEY 가 필요합니다 (ROOMPILOT_PROVIDER=mock 로 우회 가능).")
        self._llm_pro = ChatUpstage(model=pro_model, temperature=0)
        self._llm_mini = ChatUpstage(model=mini_model, temperature=0)
        self._emb = UpstageEmbeddings(model="solar-embedding-1-large")

    def _structured(self, model: Any, schema: dict, messages: list) -> dict:
        return _as_dict(model.with_structured_output(schema).invoke(messages))

    # ------------------------------------------------------------------ Agent 1
    def classify_intent(self, text: str, stage: str) -> dict:
        out = self._structured(
            self._llm_mini,
            INTENT_SCHEMA,
            [{"role": "system", "content": INTENT_SYSTEM}, {"role": "user", "content": text}],
        )
        intent = out.get("intent", "chitchat")
        return {"intent": intent, "edit": out.get("edit")}

    def extract(
        self,
        text: str,
        cards: list[ConditionCard],
        asked_dimensions: list[str],
        hard: dict,
    ) -> tuple[list[ConditionCard], dict]:
        out = self._structured(
            self._llm_pro,
            EXTRACT_SCHEMA,
            [{"role": "system", "content": EXTRACT_SYSTEM}, {"role": "user", "content": text}],
        )
        new: list[ConditionCard] = []
        for raw in out.get("cards", []):
            card = self._to_card(raw, asked_dimensions)
            if card is not None:
                new.append(card)
        updates: dict = {}
        for c in new:
            if c.kind == "hard":
                updates.update(_card_to_hard(c, text))
        return new, updates

    def discover_question(self, category: str, desc: str, cards: list[ConditionCard]) -> str:
        prompt = (
            f"사용자의 생활 맥락에서 '{desc}'({category}) 차원을 공감+근거 형태로 한 문장 역질문해라. "
            "설문처럼 묻지 말고 자연스럽게."
        )
        return message_text(self._llm_pro.invoke([{"role": "user", "content": prompt}]).content)

    # ------------------------------------------------------------------ Agent 2
    def embed(self, text: str) -> list[float]:
        return self._emb.embed_query(text)

    def score_listing(
        self, listing: Listing, cards: list[ConditionCard]
    ) -> tuple[list[MatchResult], str | None]:
        soft = [c for c in cards if c.kind == "soft"]
        # transit/commute 는 desc가 아니라 geo 사실 → LLM에 맡기지 않고 결정적으로 채운다.
        desc_cards = [c for c in soft if c.category not in ("transit", "commute")]
        breakdown: list[MatchResult] = []
        tradeoff: str | None = None
        if desc_cards:
            out = self._structured(
                self._llm_pro,
                SCORE_SCHEMA,
                [
                    {"role": "system", "content": SCORE_SYSTEM},
                    {"role": "user", "content": _format_score_payload(listing, desc_cards)},
                ],
            )
            valid_ids = {c.id for c in desc_cards}
            for b in out.get("breakdown", []):
                cid = b.get("card_id")
                if cid not in valid_ids:
                    continue
                status = b.get("status")
                breakdown.append(
                    MatchResult(
                        card_id=cid,
                        status=status if status in VALID_STATUS else "none",
                        evidence=b.get("evidence", "") or "",
                    )
                )
            tradeoff = out.get("tradeoff")
        self._fill_geo(listing, soft, breakdown)  # geo 카드(역/캠퍼스 도보) 결정적 채움
        return breakdown, tradeoff

    def check_grounded(self, context: str, answer: str) -> str:
        # Upstage groundedness-check 전용 모델 폐기 → LLM-as-Judge(solar-pro2, Practice09).
        if not answer:
            return "notSure"
        out = self._structured(
            self._llm_pro,
            GROUNDEDNESS_SCHEMA,
            [
                {"role": "system", "content": GROUNDEDNESS_SYSTEM},
                {"role": "user", "content": f"[context]\n{context}\n\n[answer]\n{answer}"},
            ],
        )
        verdict = out.get("verdict")
        return verdict if verdict in VALID_VERDICT else "notSure"

    # ------------------------------------------------------------------ Agent 3
    def analyze_location(
        self, listing: Listing, cards: list[ConditionCard], priority_order: list[str]
    ) -> dict:
        # 입지 raw(geo/location)를 카드 관점으로 번역. geo_cache(OSM 실측)가 있으면 그 출처를 보존.
        loc = dict(listing.location)
        loc.setdefault("dataSource", "seed")
        return loc

    # ------------------------------------------------------------- internals
    def _to_card(self, c: dict, asked: list[str]) -> ConditionCard | None:
        category = c.get("category")
        if category not in VALID_CATEGORIES:
            return None  # enum 이탈 카드는 버린다(환각/잡음 차단)
        kind = c.get("kind") if c.get("kind") in ("hard", "soft") else "soft"
        source = c.get("source") if c.get("source") in ("said", "extracted") else "extracted"
        if asked and source != "said" and category == asked[-1]:
            source = "discovered"
        return ConditionCard(
            id=f"c_{category}",
            label=c.get("label", category),
            category=category,
            kind=kind,
            source=source,
            reason=c.get("reason", ""),
        )

    def _fill_geo(
        self, listing: Listing, soft: list[ConditionCard], breakdown: list[MatchResult]
    ) -> None:
        have = {m.card_id for m in breakdown}
        for c in soft:
            if c.category in ("transit", "commute") and c.id not in have:
                key = "station_walk_min" if c.category == "transit" else "campus_walk_min"
                wm = int(listing.geo.get(key, 99))
                breakdown.append(
                    MatchResult(card_id=c.id, status=match_geo(c.category, wm), evidence=f"도보 {wm}분")
                )


def _format_score_payload(listing: Listing, cards: list[ConditionCard]) -> str:
    """LLM 점수화 입력을 사람이 읽기 좋은 형태로 정리(원시 dict 문자열화 대신)."""
    lines = [
        f"[매물] {listing.name} ({listing.area})",
        f"[설명] {listing.desc}",
        "",
        "[판정할 조건]",
    ]
    for c in cards:
        lines.append(f'- card_id={c.id} | {c.label}({c.category}): 사용자 근거 "{c.reason}"')
    return "\n".join(lines)


def _card_to_hard(card: ConditionCard, text: str) -> dict:
    """하드 카드 → 제약 dict. 위치 기반 nums[0]/nums[1] 대신 라벨 기반 파싱."""
    if card.category == "area":
        return {"area": "부산대"}
    if card.category == "budget":
        out: dict = {}
        dep = won_after(text, ["보증금"])
        rent = won_after(text, ["월세"])
        mgmt = won_after(text, ["관리비"])
        if dep is not None:
            out["deposit"] = dep
        if rent is not None:
            out["rent"] = rent
        if mgmt is not None:
            out["mgmt_fee_max"] = mgmt
        return out
    return {}
