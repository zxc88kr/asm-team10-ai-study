"""시드 매물 좌표를 OSM 공공데이터로 enrich → app/data/geo_cache.json 캐시 생성.

실행: python3 scripts/enrich_listings.py
- 각 매물 좌표로 Overpass(주변 POI)/OSRM(도보 통학) 실측 호출
- 결과를 캐시에 저장하면 런타임(seed 로더)이 가정값 대신 실데이터를 사용
공개 API 예의를 위해 호출 간 약간의 지연을 둔다. 네트워크 필요.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from app.data.seed import load_listings
from app.services import osm

_OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "geo_cache.json"


def main() -> None:
    cache: dict[str, dict] = {}
    listings = load_listings()
    for i, listing in enumerate(listings):
        lat = listing.geo.get("lat")
        lng = listing.geo.get("lng")
        if lat is None or lng is None:
            print(f"[skip] {listing.id} 좌표 없음")
            continue
        print(f"[{i + 1}/{len(listings)}] {listing.id} {listing.name} enrich…")
        try:
            facts = osm.fetch_facts(float(lat), float(lng))
        except (RuntimeError, OSError) as exc:
            print(f"    [warn] enrich 실패 → 시드 유지: {exc}")
            continue
        location = osm.build_location(facts)
        geo = {
            "lat": facts["lat"],
            "lng": facts["lng"],
            "campus_walk_min": facts["campusWalkMin"],
            "station_walk_min": facts["stationWalkMin"] or listing.geo.get("station_walk_min"),
            "subway": listing.geo.get("subway"),
            "line": listing.geo.get("line"),
            "counts": facts["counts"],
        }
        cache[listing.id] = {
            "geo": geo,
            "location": location,
            "fetchedAt": datetime.now(UTC).isoformat(),
            "source": osm.DATA_SOURCE,
        }
        c = facts["counts"]
        print(
            f"    통학 {facts['campusWalkMin']}분 · 편의점 {c['convenience']} · "
            f"마트 {c['supermarket']} · 가로등 {c['street_lamp']} · 경찰 {c['police']}"
        )
        time.sleep(3.0)  # 공개 API 예의(레이트리밋 회피)

    _OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {_OUT} ({len(cache)}건)")


if __name__ == "__main__":
    main()
