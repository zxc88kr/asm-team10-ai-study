"""OpenStreetMap 공공데이터 기반 입지 enrich (키 불필요, ODbL).

- Nominatim: 주소 → 좌표(지오코딩)
- Overpass: 좌표 주변 실제 POI(편의점·마트·지하철·경찰·가로등 등)
- OSRM: 도보 실측 경로(매물 → 캠퍼스)

네트워크 호출 함수와, 응답을 입지 카드로 변환하는 순수 함수(테스트 대상)를 분리한다.
시드 매물의 입지 수치를 "가정값"에서 "실측/실데이터"로 바꾸는 것이 목적.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from typing import Any

import httpx

# 부산대학교 정문(데모 기준점) — Nominatim 실측 좌표
CAMPUS_LAT = 35.2332
CAMPUS_LNG = 129.0794

_RADIUS_M = 800
_WALK_M_PER_MIN = 75.0  # 도보 속도 가정(약 4.5km/h)
_USER_AGENT = "RoomPilot/0.1 (demo; +https://github.com/zxc88kr/asm-team10-ai-study)"

DATA_SOURCE = "OpenStreetMap(ODbL) · OSRM 실측"

# Overpass 태그 → 카테고리 판정. 한 좌표 주변에서 카테고리별 최근접/개수를 집계한다.
_CATEGORIES: dict[str, Callable[[dict[str, Any]], bool]] = {
    "convenience": lambda t: t.get("shop") == "convenience",
    "supermarket": lambda t: t.get("shop") in ("supermarket", "mall", "department_store"),
    "cafe": lambda t: t.get("amenity") == "cafe",
    "pharmacy": lambda t: t.get("amenity") == "pharmacy",
    "hospital": lambda t: t.get("amenity") in ("hospital", "clinic", "doctors"),
    "police": lambda t: t.get("amenity") == "police",
    "subway": lambda t: t.get("station") == "subway" or t.get("railway") == "station",
    "bus": lambda t: t.get("highway") == "bus_stop",
    "street_lamp": lambda t: t.get("highway") == "street_lamp",
}


# ──────────────────────────────────────────────────────────── 순수 함수
def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 좌표 간 대원 거리(m)."""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def walk_min(distance_m: float) -> int:
    """도보 분(최소 1분)."""
    return max(1, round(distance_m / _WALK_M_PER_MIN))


def parse_osrm(payload: dict[str, Any]) -> dict[str, int] | None:
    """OSRM route 응답 → {minutes, distanceM}. 실패 시 None."""
    routes = payload.get("routes") or []
    if not routes:
        return None
    route = routes[0]
    duration = route.get("duration")
    distance = route.get("distance")
    if duration is None or distance is None:
        return None
    return {"minutes": max(1, round(float(duration) / 60)), "distanceM": round(float(distance))}


def parse_overpass(payload: dict[str, Any], lat: float, lng: float) -> dict[str, Any]:
    """Overpass 응답을 카테고리별 최근접 거리/개수로 집계."""
    nearest: dict[str, dict[str, Any]] = {}
    counts: dict[str, int] = {k: 0 for k in _CATEGORIES}
    for el in payload.get("elements", []):
        plat = el.get("lat", el.get("center", {}).get("lat"))
        plng = el.get("lon", el.get("center", {}).get("lon"))
        if plat is None or plng is None:
            continue
        tags = el.get("tags", {}) or {}
        dist = haversine_m(lat, lng, float(plat), float(plng))
        for cat, match in _CATEGORIES.items():
            if not match(tags):
                continue
            counts[cat] += 1
            cur = nearest.get(cat)
            if cur is None or dist < cur["distanceM"]:
                nearest[cat] = {
                    "distanceM": round(dist),
                    "walkMin": walk_min(dist),
                    "name": tags.get("name", ""),
                }
    return {"nearest": nearest, "counts": counts}


_CONV_LABEL = {
    "convenience": ("편의점", "shopping-bag"),
    "supermarket": ("마트", "shopping-cart"),
    "cafe": ("카페", "coffee"),
    "pharmacy": ("약국", "pill"),
    "hospital": ("병원", "stethoscope"),
}


def build_location(facts: dict[str, Any]) -> dict[str, Any]:
    """실측 facts → 프론트/점수화가 쓰는 입지 카드(commute/nightSafety/convenience/pros/cons)."""
    nearest: dict[str, Any] = facts.get("nearest", {})
    counts: dict[str, int] = facts.get("counts", {})
    campus_min = int(facts.get("campusWalkMin", 0))
    station = nearest.get("subway")

    legs: list[dict[str, Any]] = [{"label": "집", "minutes": 0, "type": "walk"}]
    if station and station["walkMin"] <= 12:
        legs.append({"label": station.get("name") or "지하철역", "minutes": station["walkMin"], "type": "subway"})
    legs.append({"label": "부산대 정문", "minutes": campus_min, "type": "walk"})

    night = _night_safety(nearest, counts)
    convenience = _convenience(nearest)
    pros, cons = _pros_cons(nearest, counts, campus_min, night)

    return {
        "commute": {
            "legs": legs,
            "totalMinutes": campus_min,
            "transfers": 0,
            "mainNote": f"부산대 정문까지 도보 약 {campus_min}분 (OSRM 실측)",
        },
        "nightSafety": night,
        "convenience": convenience,
        "pros": pros,
        "cons": cons,
        "aiComment": _summary(nearest, campus_min, night),
        "dataSource": DATA_SOURCE,
        "facts": {"counts": counts, "nearest": nearest, "campusWalkMin": campus_min},
    }


def _night_safety(nearest: dict[str, Any], counts: dict[str, int]) -> list[dict[str, Any]]:
    conv = nearest.get("convenience")
    police = nearest.get("police")
    lamps = counts.get("street_lamp", 0)
    items: list[dict[str, Any]] = []
    if conv:
        ok = conv["distanceM"] <= 250
        items.append({
            "icon": "shopping-bag",
            "label": "심야 편의점 근접" if ok else "편의점 다소 거리",
            "detail": f"가장 가까운 편의점 도보 {conv['walkMin']}분",
            "pass": ok,
        })
    if lamps > 0:  # OSM 미수록 지역은 '적음'으로 단정하지 않음(환각 방지)
        lamp_ok = lamps >= 8
        items.append({
            "icon": "lightbulb",
            "label": "가로등 분포 양호" if lamp_ok else "가로등 다소 적음",
            "detail": f"반경 800m 내 가로등 {lamps}개 (OSM)",
            "pass": lamp_ok,
        })
    if police:
        items.append({
            "icon": "shield",
            "label": "인근 지구대·파출소",
            "detail": f"도보 약 {police['walkMin']}분",
            "pass": True,
        })
    return items


def _convenience(nearest: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cat, (name, icon) in _CONV_LABEL.items():
        hit = nearest.get(cat)
        if hit:
            out.append({"name": name, "walkMin": hit["walkMin"], "icon": icon})
    return out


def _pros_cons(
    nearest: dict[str, Any], counts: dict[str, int], campus_min: int, night: list[dict[str, Any]]
) -> tuple[list[str], list[str]]:
    pros: list[str] = []
    cons: list[str] = []
    if campus_min <= 15:
        pros.append(f"부산대 정문 도보 {campus_min}분 (가까움)")
    else:
        cons.append(f"부산대 정문까지 도보 {campus_min}분 (다소 멀음)")
    conv = nearest.get("convenience")
    if conv and conv["walkMin"] <= 3:
        pros.append(f"편의점 도보 {conv['walkMin']}분")
    mart = nearest.get("supermarket")
    if mart:
        pros.append(f"마트 도보 {mart['walkMin']}분")
    lamps = counts.get("street_lamp", 0)
    if lamps == 0:
        cons.append("가로등 데이터 미수록 — 야간 동선 직접 확인 권장")
    elif any(n["icon"] == "lightbulb" and not n["pass"] for n in night):
        cons.append("가로등이 다소 적어 야간 동선 확인 필요")
    if not nearest.get("subway"):
        cons.append("반경 내 지하철역 없음(버스 위주)")
    return pros, cons


def _summary(nearest: dict[str, Any], campus_min: int, night: list[dict[str, Any]]) -> str:
    safe = sum(1 for n in night if n["pass"])
    conv = nearest.get("convenience")
    conv_txt = f"편의점 도보 {conv['walkMin']}분, " if conv else ""
    return (
        f"OSM 공공데이터 실측: 통학 도보 {campus_min}분, {conv_txt}"
        f"야간 안전 지표 {safe}/{len(night)} 충족."
    )


# ──────────────────────────────────────────────────────────── 네트워크
def _client(timeout: float = 30.0) -> httpx.Client:
    return httpx.Client(timeout=timeout, headers={"User-Agent": _USER_AGENT})


def geocode(query: str) -> tuple[float, float] | None:
    """Nominatim 지오코딩. 실패 시 None."""
    with _client() as c:
        resp = c.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
        )
        resp.raise_for_status()
        data = resp.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


def osrm_walk(lat: float, lng: float, to_lat: float, to_lng: float) -> dict[str, int] | None:
    """OSRM 도보 경로(분/거리). 실패 시 None."""
    url = f"https://router.project-osrm.org/route/v1/foot/{lng},{lat};{to_lng},{to_lat}"
    with _client() as c:
        resp = c.get(url, params={"overview": "false"})
        resp.raise_for_status()
        return parse_osrm(resp.json())


def overpass_around(lat: float, lng: float, radius: int = _RADIUS_M) -> dict[str, Any]:
    """Overpass 주변 POI 집계."""
    selectors = [
        "[shop=convenience]",
        '[shop~"supermarket|mall|department_store"]',
        "[amenity=cafe]",
        "[amenity=pharmacy]",
        '[amenity~"hospital|clinic|doctors"]',
        "[amenity=police]",
        "[station=subway]",
        "[railway=station]",
        "[highway=bus_stop]",
        "[highway=street_lamp]",
    ]
    body = "".join(f"node(around:{radius},{lat},{lng}){s};" for s in selectors)
    query = f"[out:json][timeout:25];({body});out body;"
    payload = _overpass_post(query)
    return parse_overpass(payload, lat, lng)


_OVERPASS_MIRRORS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
)


def _overpass_post(query: str, retries: int = 3) -> dict[str, Any]:
    """Overpass POST — 미러 순회 + 429/일시 오류 백오프 재시도."""
    last: Exception | None = None
    for attempt in range(retries):
        for url in _OVERPASS_MIRRORS:
            try:
                with _client(50.0) as c:
                    resp = c.post(url, data={"data": query})
                if resp.status_code in (429, 503, 504):
                    last = httpx.HTTPStatusError(f"{resp.status_code}", request=resp.request, response=resp)
                    continue
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, ValueError) as exc:  # 네트워크/JSON 오류 → 다음 미러
                last = exc
                continue
        time.sleep(2.0 * (attempt + 1))  # 백오프 후 재시도
    raise RuntimeError(f"overpass failed: {last}")


def fetch_facts(lat: float, lng: float) -> dict[str, Any]:
    """매물 좌표 → 실측 입지 facts (OSRM 통학 + Overpass 주변)."""
    agg = overpass_around(lat, lng)
    walk = osrm_walk(lat, lng, CAMPUS_LAT, CAMPUS_LNG)
    campus_min = walk["minutes"] if walk else walk_min(haversine_m(lat, lng, CAMPUS_LAT, CAMPUS_LNG))
    station = agg["nearest"].get("subway")
    return {
        "lat": lat,
        "lng": lng,
        "campusWalkMin": campus_min,
        "campusWalkM": walk["distanceM"] if walk else None,
        "stationWalkMin": station["walkMin"] if station else None,
        "nearest": agg["nearest"],
        "counts": agg["counts"],
    }
