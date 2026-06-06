"""시드 매물 로더.

데모 매물은 시드(가상) 데이터이며 실거래 매물이 아니다. 입지 수치는 데모용 가정값.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

_DATA_PATH = Path(__file__).with_name("listings.json")


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


@lru_cache(maxsize=1)
def load_listings() -> list[Listing]:
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return [Listing(**item) for item in raw]


def get_listing(listing_id: str) -> Listing:
    for listing in load_listings():
        if listing.id == listing_id:
            return listing
    raise KeyError(f"unknown listing: {listing_id}")
