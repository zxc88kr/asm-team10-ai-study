"""OSM 입지 enrich 순수 함수 테스트 (네트워크 미사용 — 응답 픽스처로 검증)."""

from __future__ import annotations

from app.services import osm


def test_haversine_and_walk_min() -> None:
    # 부산대 정문 ↔ 인근 좌표(약 600~700m) → 도보 약 8~10분
    d = osm.haversine_m(osm.CAMPUS_LAT, osm.CAMPUS_LNG, 35.2298, 129.0865)
    assert 500 < d < 900
    assert osm.walk_min(0) == 1  # 최소 1분
    assert osm.walk_min(150) == 2


def test_parse_osrm() -> None:
    payload = {"code": "Ok", "routes": [{"duration": 216.1, "distance": 1181.4}]}
    out = osm.parse_osrm(payload)
    assert out == {"minutes": 4, "distanceM": 1181}
    assert osm.parse_osrm({"routes": []}) is None


def test_parse_overpass_counts_and_nearest() -> None:
    lat, lng = 35.2300, 129.0860
    payload = {
        "elements": [
            {"lat": 35.2301, "lon": 129.0861, "tags": {"shop": "convenience", "name": "CU"}},
            {"lat": 35.2330, "lon": 129.0890, "tags": {"shop": "convenience", "name": "GS25"}},
            {"lat": 35.2302, "lon": 129.0862, "tags": {"amenity": "police", "name": "장전지구대"}},
            {"lat": 35.2305, "lon": 129.0865, "tags": {"highway": "street_lamp"}},
            {"lat": 35.2306, "lon": 129.0866, "tags": {"highway": "street_lamp"}},
        ]
    }
    agg = osm.parse_overpass(payload, lat, lng)
    assert agg["counts"]["convenience"] == 2
    assert agg["counts"]["street_lamp"] == 2
    assert agg["counts"]["police"] == 1
    # 최근접 편의점은 CU(가장 가까움)
    assert agg["nearest"]["convenience"]["name"] == "CU"
    assert agg["nearest"]["convenience"]["walkMin"] >= 1


def test_build_location_from_facts() -> None:
    facts = {
        "campusWalkMin": 8,
        "nearest": {
            "convenience": {"distanceM": 120, "walkMin": 2, "name": "CU"},
            "supermarket": {"distanceM": 300, "walkMin": 4, "name": "마트"},
            "subway": {"distanceM": 400, "walkMin": 6, "name": "부산대역"},
            "police": {"distanceM": 200, "walkMin": 3, "name": "지구대"},
        },
        "counts": {"convenience": 5, "supermarket": 2, "street_lamp": 12, "police": 1},
    }
    loc = osm.build_location(facts)
    assert loc["commute"]["totalMinutes"] == 8
    # 지하철역이 12분 이내 → 지하철 leg 포함
    assert any(leg["type"] == "subway" for leg in loc["commute"]["legs"])
    # 편의점 120m(<=250) → 심야 편의점 근접 pass
    conv_item = next(n for n in loc["nightSafety"] if n["icon"] == "shopping-bag")
    assert conv_item["pass"] is True
    # 가로등 12개(>=8) → 양호
    lamp_item = next(n for n in loc["nightSafety"] if n["icon"] == "lightbulb")
    assert lamp_item["pass"] is True
    assert any("편의점" == c["name"] for c in loc["convenience"])
    assert loc["dataSource"] == osm.DATA_SOURCE
    assert "부산대 정문 도보 8분 (가까움)" in loc["pros"]


def test_build_location_missing_lamp_is_not_claimed() -> None:
    # 가로등 0(OSM 미수록) → '적음'이라 단정하지 않고 확인 권장 cons
    facts = {
        "campusWalkMin": 18,
        "nearest": {"convenience": {"distanceM": 500, "walkMin": 7, "name": "CU"}},
        "counts": {"convenience": 1, "street_lamp": 0},
    }
    loc = osm.build_location(facts)
    assert all(n["icon"] != "lightbulb" for n in loc["nightSafety"])
    assert any("가로등 데이터 미수록" in c for c in loc["cons"])
    assert any("도보 18분" in c for c in loc["cons"])  # 통학 멀면 cons
