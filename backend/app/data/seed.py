"""시드 매물 로더.

데모 매물은 시드(가상) 데이터이며 실거래 매물이 아니다. 단, 입지 수치(통학 도보·주변
편의·야간 안전)는 `geo_cache.json`이 있으면 OSM 공공데이터 실측값으로 대체한다.
(캐시는 `scripts/enrich_listings.py`가 Overpass/OSRM 실호출로 생성.)
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

_DATA_PATH = Path(__file__).with_name("listings.json")
_GEO_CACHE_PATH = Path(__file__).with_name("geo_cache.json")


class Listing(BaseModel):
    id: str
    name: str
    type: str
    area: str
    deposit: int
    rent: int
    mgmt_fee: int = 0
    pyeong: float
    floor: int
    options: list[str] = Field(default_factory=list)
    desc: str  # ★ 의미 매칭 대상 — 시드 설명 전문
    geo: dict = Field(default_factory=dict)
    location: dict = Field(default_factory=dict)
    embedding: list[float] | None = None  # 사전 계산 캐시

    def area_matches(self, area_query: str | None) -> bool:
        """부산대 인근(장전동/구서동) 매칭. query 없으면 전체 허용."""
        if not area_query:
            return True
        near = {"부산대", "장전동", "구서동", "장전", "구서"}
        if any(tok in area_query for tok in near):
            return self.area in {"장전동", "구서동"}
        return area_query in self.area


def _load_geo_cache() -> dict[str, dict[str, Any]]:
    if not _GEO_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(_GEO_CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


@lru_cache(maxsize=1)
def load_listings() -> list[Listing]:
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    cache = _load_geo_cache()
    listings: list[Listing] = []
    for item in raw:
        enriched = cache.get(item["id"])
        if enriched:  # OSM 공공데이터 실측으로 입지 수치 대체
            item = {
                **item,
                "geo": {**item.get("geo", {}), **enriched.get("geo", {})},
                "location": enriched.get("location", item.get("location", {})),
            }
        listings.append(Listing(**item))
    return listings


def get_listing(listing_id: str) -> Listing:
    for listing in load_listings():
        if listing.id == listing_id:
            return listing
    raise KeyError(f"unknown listing: {listing_id}")
