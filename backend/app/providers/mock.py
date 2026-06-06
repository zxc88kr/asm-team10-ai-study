"""결정적 Mock Provider.

API 키 없이 '민지의 첫 자취집 찾기' 시나리오를 그대로 재현한다. 키워드 규칙으로
LLM/임베딩/Groundedness 동작을 대체하므로, 그래프 전체를 오프라인에서 테스트할 수 있다.
실제 추론 품질이 아니라 '파이프라인 동작'을 결정적으로 보여주는 것이 목적이다.
"""

from __future__ import annotations

import re

from app.data.seed import Listing
from app.providers.base import Provider
from app.scoring import match_desc, match_geo
from app.state import CardSource, ConditionCard, Kind, MatchResult, MatchStatus

# 발굴 차원 → 카드 라벨
DISCOVER_LABEL = {
    "safety": "야간 안전 동선",
    "security": "택배·현관 보안",
    "light": "채광·환기",
    "noise": "방음",
    "kitchen": "분리형 주방",
}
# 임베딩용 고정 어휘(의미 매칭 데모)
EMBED_VOCAB = [
    "가로등", "편의점", "대로변", "도어락", "무인택배함", "분리형", "개방형",
    "남향", "채광", "환기", "역", "도보", "경비", "엘리베이터", "신축", "안전",
]
_NEG = ("아니", "필요 없", "필요없", "상관없", "괜찮아요 안")
_LIFESTYLE = ("11시", "요리", "알바", "본가", "학교", "통학", "밤")


def _won(text: str, keywords: list[str]) -> int | None:
    """키워드 뒤 숫자(만원 단위). '5~7만' 처럼 범위면 최댓값."""
    for kw in keywords:
        idx = text.find(kw)
        if idx == -1:
            continue
        nums = re.findall(r"\d+", text[idx : idx + 12])
        if nums:
            return max(int(n) for n in nums)
    return None


def _card(
    cid: str, label: str, cat: str, kind: Kind, source: CardSource, reason: str
) -> ConditionCard:
    return ConditionCard(
        id=cid, label=label, category=cat, kind=kind, source=source, reason=reason
    )


def _pick_sentence(desc: str, category: str) -> str:
    from app.scoring import DESC_RULES

    rule = DESC_RULES.get(category, {"pos": []})
    for sent in re.split(r"[.。]\s*", desc):
        if any(k in sent for k in rule["pos"]):
            return sent.strip()
    return desc.split(".")[0].strip()


class MockProvider(Provider):
    name = "mock"

    # ------------------------------------------------------------------ Agent 1
    def classify_intent(self, text: str, stage: str) -> dict:
        if stage == "needs":
            return {"intent": "provide_info", "edit": None}  # 니즈 단계는 항상 정보 수집
        if self._is_edit(text):
            return {"intent": "edit_condition", "edit": self._parse_edit(text)}
        if "방음" in text or ("어때" in text and self._listing_mentioned(text)):
            return {"intent": "ask_listing", "edit": None}
        if any(k in text for k in ("입지", "통학", "밤길", "막차", "역에서", "거리", "설명")):
            return {"intent": "ask_location", "edit": None}
        if any(k in text for k in ("고를", "선택", "로 할", "이걸로", "결정")):
            return {"intent": "select_listing", "edit": None}
        return {"intent": "provide_info" if stage == "needs" else "chitchat", "edit": None}

    def extract(
        self,
        text: str,
        cards: list[ConditionCard],
        asked_dimensions: list[str],
        hard: dict,
    ) -> tuple[list[ConditionCard], dict]:
        carded = {c.category for c in cards}
        new: list[ConditionCard] = []
        updates: dict = {}
        self._extract_hard(text, carded, new, updates)
        self._extract_soft(text, carded, hard, updates, new)
        self._extract_discovered(text, asked_dimensions, carded, new)
        return new, updates

    def discover_question(self, category: str, desc: str, cards: list[ConditionCard]) -> str:
        templates = {
            "safety": "밤 11시에 혼자 들어가는 길이 매일이잖아요. 집 보러 다닐 때 "
            "'이 골목 좀 무섭다' 같은 거 신경 쓰는 편이에요? 첫 자취생이 제일 후회하는 부분이라서요.",
            "security": "본가가 멀어 택배·배달을 자주 쓰실 텐데, 무인택배함이나 공동현관 "
            "보안 같은 것도 챙겨드릴까요?",
            "light": "요리를 자주 하고 오래 사실 거라, 채광·환기(곰팡이/습기)도 첫 자취 후회 "
            "1순위인데 같이 볼까요?",
            "noise": "방음도 신경 쓰는 편이세요?",
            "kitchen": "주방이 분리돼 있는 게 좋을까요?",
        }
        return templates.get(category, f"{desc}, 신경 쓰는 편이세요?")

    # ------------------------------------------------------------------ Agent 2
    def embed(self, text: str) -> list[float]:
        return [float(text.count(tok)) for tok in EMBED_VOCAB]

    def score_listing(
        self, listing: Listing, cards: list[ConditionCard]
    ) -> tuple[list[MatchResult], str | None]:
        breakdown: list[MatchResult] = []
        for c in cards:
            if c.kind != "soft":
                continue
            status, evidence = self._judge(listing, c)
            breakdown.append(
                MatchResult(card_id=c.id, status=status, evidence=evidence)
            )
        return breakdown, self._tradeoff(breakdown, cards)

    def check_grounded(self, context: str, answer: str) -> str:
        if not answer:
            return "notSure"
        return "grounded" if answer[:12] in context else "notGrounded"

    # ------------------------------------------------------------------ Agent 3
    def analyze_location(
        self, listing: Listing, cards: list[ConditionCard], priority_order: list[str]
    ) -> dict:
        loc = dict(listing.location)
        loc["basis"] = self._basis(cards, priority_order, listing)
        loc["scoreBreakdown"] = self._loc_scores(listing)
        loc["dataSource"] = "seed"
        return loc

    # ------------------------------------------------------------- internals
    def _extract_hard(
        self, text: str, carded: set[str], new: list[ConditionCard], updates: dict
    ) -> None:
        if ("부산대" in text or "장전" in text) and "area" not in carded:
            new.append(_card("c_area", "지역", "area", "hard", "said", "부산대 신입"))
            updates["area"] = "부산대"
        dep = _won(text, ["보증금", "보 "])
        rent = _won(text, ["월세", "월 "])
        if (dep or rent) and "budget" not in carded:
            new.append(_card("c_budget", "예산", "budget", "hard", "said", text[:40]))
        if dep:
            updates["deposit"] = dep
        if rent:
            updates["rent"] = rent
        mgmt = _won(text, ["관리비"])
        if mgmt:
            updates["mgmt_fee_max"] = mgmt

    def _extract_soft(
        self,
        text: str,
        carded: set[str],
        hard: dict,
        updates: dict,
        new: list[ConditionCard],
    ) -> None:
        if ("11시" in text or "밤" in text) and "transit" not in carded:
            new.append(_card("c_transit", "심야 교통", "transit", "soft", "extracted", text[:40]))
        if "요리" in text and "kitchen" not in carded:
            new.append(_card("c_kitchen", "분리형 주방", "kitchen", "soft", "extracted", "요리 자주"))
        area_known = "area" in carded or "area" in updates or hard.get("area")
        if area_known and "commute" not in carded and any(k in text for k in _LIFESTYLE):
            new.append(_card("c_commute", "통학 부담", "commute", "soft", "extracted", "부산대 신입"))

    def _extract_discovered(
        self, text: str, asked_dimensions: list[str], carded: set[str], new: list[ConditionCard]
    ) -> None:
        if not asked_dimensions:
            return
        last = asked_dimensions[-1]
        if last in carded or any(n in text for n in _NEG):
            return
        label = DISCOVER_LABEL.get(last, last)
        new.append(_card(f"c_{last}", label, last, "soft", "discovered", f"(추론) {text[:30]}"))

    def _judge(self, listing: Listing, card: ConditionCard) -> tuple[MatchStatus, str]:
        if card.category in ("transit", "commute"):
            key = "station_walk_min" if card.category == "transit" else "campus_walk_min"
            wm = int(listing.geo.get(key, 99))
            status = match_geo(card.category, wm)
            sub = listing.geo.get("subway", "역") if card.category == "transit" else "캠퍼스"
            return status, f"{sub} 도보 {wm}분" if status != "none" else ""
        status = match_desc(card.category, listing.desc)
        return status, (_pick_sentence(listing.desc, card.category) if status != "none" else "")

    def _tradeoff(
        self, breakdown: list[MatchResult], cards: list[ConditionCard]
    ) -> str | None:
        by = {m.card_id: m for m in breakdown}
        safety_ok = any(
            by.get(c.id) and by[c.id].status == "full"
            for c in cards if c.category == "safety"
        )
        weak = [
            c.label for c in cards
            if c.category in ("kitchen", "light") and by.get(c.id) and by[c.id].status == "none"
        ]
        if safety_ok and weak:
            return f"안전 최상 ↔ {'·'.join(weak)} 아쉬움"
        return None

    def _basis(
        self, cards: list[ConditionCard], priority_order: list[str], listing: Listing
    ) -> list[dict]:
        colors = {"safety": "#F59E0B", "transit": "#4B7BF5", "commute": "#22C55E"}
        out = []
        for cat in (priority_order or ["safety"])[:3]:
            label = next((c.label for c in cards if c.category == cat), cat)
            out.append({"category": label, "color": colors.get(cat, "#8B5CF6"), "detail": ""})
        return out

    def _loc_scores(self, listing: Listing) -> list[dict]:
        wm = int(listing.geo.get("campus_walk_min", 15))
        return [
            {"label": "심야 귀가", "score": 90 if listing.geo.get("lit") else 60},
            {"label": "통학", "score": max(100 - wm * 3, 50)},
        ]

    def _is_edit(self, text: str) -> bool:
        has_money = ("월세" in text or "보증금" in text or "예산" in text)
        has_op = any(k in text for k in ("올리", "내리", "낮춰", "더", "추가", "로 ", "으로"))
        return has_money and has_op and bool(re.search(r"\d", text))

    def _parse_edit(self, text: str) -> dict:
        field = "deposit" if ("보증금" in text or "보증" in text) else "rent"
        nums = re.findall(r"\d+", text)
        value = int(nums[0]) if nums else 0
        if any(k in text for k in ("올리", "더", "추가")):
            op = "inc"
        elif any(k in text for k in ("내리", "낮춰", "빼")):
            op = "dec"
        else:
            op = "set"
        return {"field": field, "op": op, "value": value}

    def _listing_mentioned(self, text: str) -> bool:
        return any(tok in text for tok in ("A", "B", "C", "D", "빌라", "오피스텔", "원룸"))
