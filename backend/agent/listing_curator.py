from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from .schema import ConditionState
from .solar_client import SolarClientError, call_upstage_chat_content, get_solar_api_key


MOCK_PROPERTIES: list[dict[str, Any]] = [
    # ── 강남구 (강남역 8-13분) ──────────────────────────────────────────────
    {
        "id": "P001",
        "type": "원룸",
        "title": "선릉역 역세권 원룸 4층",
        "deposit": 1000,
        "monthly_rent": 75,
        "location": "서울 강남구 역삼동",
        "address_detail": "선릉역 2번 출구 도보 5분",
        "description": (
            "4층 남향 원룸으로 채광이 뛰어납니다. "
            "건물 입구·복도 CCTV 설치, 반지하 아님. "
            "에어컨·세탁기·냉장고 풀옵션. "
            "벌레·곰팡이 이력 없는 깨끗한 건물. "
            "편의점 도보 2분, 약국 5분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "선릉역", "walk_min": 5},
        "lat": 37.5048,
        "lng": 127.0493,
        "commute_legs": [
            {"type": "walk", "label": "집 → 선릉역", "minutes": 5},
            {"type": "subway", "label": "선릉역 → 강남역 (2호선)", "minutes": 3},
        ],
        "commute_total_minutes": 8,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 입구·복도 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "4층 남향 채광 우수", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 2분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 2, "icon": "store"},
            {"name": "약국", "walk_min": 5, "icon": "pill"},
            {"name": "카페", "walk_min": 4, "icon": "coffee"},
        ],
    },
    {
        "id": "P002",
        "type": "오피스텔",
        "title": "역삼역 신축 오피스텔 12층",
        "deposit": 2000,
        "monthly_rent": 98,
        "location": "서울 강남구 역삼동",
        "address_detail": "역삼역 1번 출구 도보 3분",
        "description": (
            "2023년 신축 오피스텔, 12층 탁 트인 조망. "
            "풀옵션(에어컨, 세탁기, 냉장고, 전자레인지, 인덕션) 포함. "
            "24시간 경비·CCTV, 벌레·곰팡이 이력 없음. "
            "편의점·마트·카페 도보 3분 이내."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "전자레인지", "인덕션", "CCTV"],
        "transit": {"station": "역삼역", "walk_min": 3},
        "lat": 37.5006,
        "lng": 127.0368,
        "commute_legs": [
            {"type": "walk", "label": "집 → 역삼역", "minutes": 3},
            {"type": "subway", "label": "역삼역 → 강남역 (2호선)", "minutes": 2},
        ],
        "commute_total_minutes": 5,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "24시간 경비·전층 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "12층 조망 우수", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·마트 도보 3분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 2, "icon": "store"},
            {"name": "마트", "walk_min": 3, "icon": "shopping-cart"},
            {"name": "카페", "walk_min": 2, "icon": "coffee"},
            {"name": "약국", "walk_min": 4, "icon": "pill"},
        ],
    },
    {
        "id": "P003",
        "type": "빌라",
        "title": "삼성역 인근 분리형 빌라 3층",
        "deposit": 1000,
        "monthly_rent": 82,
        "location": "서울 강남구 삼성동",
        "address_detail": "삼성역 5번 출구 도보 8분",
        "description": (
            "분리형 구조로 방과 주방이 독립되어 있습니다. "
            "3층 남향, 채광이 좋고 환기 우수. "
            "에어컨·세탁기·냉장고 포함. CCTV 설치. "
            "벌레·곰팡이 이력 없는 관리 잘 된 건물. "
            "편의점 도보 3분, 마트 5분."
        ),
        "facilities": ["분리형주방", "에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "삼성역", "walk_min": 8},
        "lat": 37.5090,
        "lng": 127.0632,
        "commute_legs": [
            {"type": "walk", "label": "집 → 삼성역", "minutes": 8},
            {"type": "subway", "label": "삼성역 → 선릉역 → 강남역 (2호선)", "minutes": 5},
        ],
        "commute_total_minutes": 13,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 입구 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "3층 남향", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 3분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 3, "icon": "store"},
            {"name": "마트", "walk_min": 5, "icon": "shopping-cart"},
            {"name": "약국", "walk_min": 7, "icon": "pill"},
        ],
    },
    # ── 서초구 (강남역 12-20분) ────────────────────────────────────────────
    {
        "id": "P004",
        "type": "오피스텔",
        "title": "서초역 직결 오피스텔 8층",
        "deposit": 2000,
        "monthly_rent": 92,
        "location": "서울 서초구 서초동",
        "address_detail": "서초역 3번 출구 도보 4분",
        "description": (
            "8층 오피스텔, 조망 우수. "
            "풀옵션(에어컨, 세탁기, 냉장고, 전자레인지) 포함. "
            "24시간 경비·CCTV, 반지하 아님. "
            "벌레·곰팡이 이력 없음. 편의점·카페 도보 3분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "전자레인지", "CCTV"],
        "transit": {"station": "서초역", "walk_min": 4},
        "lat": 37.4836,
        "lng": 127.0116,
        "commute_legs": [
            {"type": "walk", "label": "집 → 서초역", "minutes": 4},
            {"type": "subway", "label": "서초역 → 강남역 (3호선)", "minutes": 3},
        ],
        "commute_total_minutes": 7,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "24시간 경비·CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "8층 조망 우수", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·카페 도보 3분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 2, "icon": "store"},
            {"name": "카페", "walk_min": 3, "icon": "coffee"},
            {"name": "약국", "walk_min": 6, "icon": "pill"},
        ],
    },
    {
        "id": "P005",
        "type": "원룸",
        "title": "방배역 조용한 원룸 2층",
        "deposit": 500,
        "monthly_rent": 63,
        "location": "서울 서초구 방배동",
        "address_detail": "방배역 1번 출구 도보 7분",
        "description": (
            "주택가 위치로 조용하고 주차 가능. "
            "2층 원룸, 에어컨·세탁기·냉장고 포함. "
            "반지하 아님, 벌레 민원 없음. "
            "편의점 5분, 마트 8분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고"],
        "transit": {"station": "방배역", "walk_min": 7},
        "lat": 37.4815,
        "lng": 126.9976,
        "commute_legs": [
            {"type": "walk", "label": "집 → 방배역", "minutes": 7},
            {"type": "subway", "label": "방배역 → 서초역 → 강남역 (3호선 또는 2호선)", "minutes": 8},
        ],
        "commute_total_minutes": 15,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "정보 없음", "pass": False},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "2층, 일반 채광", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 5, "icon": "store"},
            {"name": "마트", "walk_min": 8, "icon": "shopping-cart"},
        ],
    },
    # ── 동작구 (강남역 20-28분) ────────────────────────────────────────────
    {
        "id": "P006",
        "type": "빌라",
        "title": "사당역 역세권 빌라 3층",
        "deposit": 700,
        "monthly_rent": 60,
        "location": "서울 동작구 사당동",
        "address_detail": "사당역 2번 출구 도보 6분",
        "description": (
            "사당역 초역세권, 3층 빌라. "
            "에어컨·세탁기·냉장고 포함. "
            "건물 CCTV 설치, 반지하 아님. "
            "편의점·마트·약국 도보 5분 이내. "
            "벌레·곰팡이 이력 없는 깨끗한 건물."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "사당역", "walk_min": 6},
        "lat": 37.4764,
        "lng": 126.9818,
        "commute_legs": [
            {"type": "walk", "label": "집 → 사당역", "minutes": 6},
            {"type": "subway", "label": "사당역 → 교대역 → 강남역 (2호선·4호선 환승)", "minutes": 16},
        ],
        "commute_total_minutes": 22,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 입구 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "3층 채광 양호", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·마트 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 3, "icon": "store"},
            {"name": "마트", "walk_min": 5, "icon": "shopping-cart"},
            {"name": "약국", "walk_min": 4, "icon": "pill"},
        ],
    },
    {
        "id": "P007",
        "type": "원룸",
        "title": "이수역 원룸 5층",
        "deposit": 500,
        "monthly_rent": 58,
        "location": "서울 동작구 대방동",
        "address_detail": "이수역(총신대입구) 7번 출구 도보 5분",
        "description": (
            "5층 원룸으로 조망 좋고 채광 우수. "
            "에어컨·세탁기·냉장고 포함. "
            "CCTV 설치, 곰팡이 없음. "
            "편의점 도보 3분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "이수역", "walk_min": 5},
        "lat": 37.4856,
        "lng": 126.9820,
        "commute_legs": [
            {"type": "walk", "label": "집 → 이수역", "minutes": 5},
            {"type": "subway", "label": "이수역 → 강남역 (4호선·2호선 환승)", "minutes": 18},
        ],
        "commute_total_minutes": 23,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 CCTV 설치", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "5층 조망 우수", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 3분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 3, "icon": "store"},
            {"name": "카페", "walk_min": 6, "icon": "coffee"},
        ],
    },
    # ── 송파구 (강남역 20-28분) ────────────────────────────────────────────
    {
        "id": "P008",
        "type": "오피스텔",
        "title": "잠실역 오피스텔 10층",
        "deposit": 2000,
        "monthly_rent": 82,
        "location": "서울 송파구 잠실동",
        "address_detail": "잠실역 3번 출구 도보 5분",
        "description": (
            "10층 오피스텔, 탁 트인 조망. "
            "풀옵션(에어컨, 세탁기, 냉장고, 전자레인지) 포함. "
            "24시간 경비·CCTV, 반지하 아님. "
            "편의점·마트·카페 도보 3분 이내. "
            "벌레·곰팡이 이력 없음."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "전자레인지", "CCTV"],
        "transit": {"station": "잠실역", "walk_min": 5},
        "lat": 37.5135,
        "lng": 127.1000,
        "commute_legs": [
            {"type": "walk", "label": "집 → 잠실역", "minutes": 5},
            {"type": "subway", "label": "잠실역 → 삼성역 → 강남역 (2호선)", "minutes": 12},
        ],
        "commute_total_minutes": 17,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "24시간 경비·CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "10층 조망 우수", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·마트 도보 3분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 2, "icon": "store"},
            {"name": "마트", "walk_min": 3, "icon": "shopping-cart"},
            {"name": "카페", "walk_min": 3, "icon": "coffee"},
            {"name": "약국", "walk_min": 5, "icon": "pill"},
        ],
    },
    {
        "id": "P009",
        "type": "원룸",
        "title": "석촌역 원룸 4층",
        "deposit": 500,
        "monthly_rent": 63,
        "location": "서울 송파구 석촌동",
        "address_detail": "석촌역 1번 출구 도보 6분",
        "description": (
            "4층 남향 원룸, 채광 좋음. "
            "에어컨·세탁기·냉장고 포함. CCTV 설치. "
            "벌레 이력 없음, 곰팡이 없음. "
            "편의점 도보 4분, 카페 5분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "석촌역", "walk_min": 6},
        "lat": 37.5040,
        "lng": 127.1042,
        "commute_legs": [
            {"type": "walk", "label": "집 → 석촌역", "minutes": 6},
            {"type": "subway", "label": "석촌역 → 강남역 (8호선·2호선 환승)", "minutes": 18},
        ],
        "commute_total_minutes": 24,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 CCTV 설치", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "4층 남향", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 4분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 4, "icon": "store"},
            {"name": "카페", "walk_min": 5, "icon": "coffee"},
            {"name": "약국", "walk_min": 8, "icon": "pill"},
        ],
    },
    # ── 성동구 (강남역 22-28분) ────────────────────────────────────────────
    {
        "id": "P010",
        "type": "오피스텔",
        "title": "성수역 트렌디 오피스텔 7층",
        "deposit": 2000,
        "monthly_rent": 88,
        "location": "서울 성동구 성수동",
        "address_detail": "성수역 3번 출구 도보 5분",
        "description": (
            "성수동 핫플 인근 7층 오피스텔. "
            "풀옵션(에어컨, 세탁기, 냉장고) 포함. "
            "건물 CCTV·경비 설치. 반지하 아님. "
            "카페·마트·편의점 도보 5분 이내. "
            "벌레·곰팡이 이력 없음."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "성수역", "walk_min": 5},
        "lat": 37.5440,
        "lng": 127.0564,
        "commute_legs": [
            {"type": "walk", "label": "집 → 성수역", "minutes": 5},
            {"type": "subway", "label": "성수역 → 건대입구역 → 강남역 (2호선)", "minutes": 22},
        ],
        "commute_total_minutes": 27,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 경비·CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "7층 채광 우수", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "카페·편의점 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 3, "icon": "store"},
            {"name": "마트", "walk_min": 5, "icon": "shopping-cart"},
            {"name": "카페", "walk_min": 2, "icon": "coffee"},
        ],
    },
    {
        "id": "P011",
        "type": "빌라",
        "title": "뚝섬역 분리형 빌라 2층",
        "deposit": 1000,
        "monthly_rent": 72,
        "location": "서울 성동구 성수동",
        "address_detail": "뚝섬역 2번 출구 도보 8분",
        "description": (
            "분리형 구조, 방과 주방 독립. "
            "2층 남향, 채광 양호. "
            "에어컨·세탁기·냉장고 포함. "
            "곰팡이·벌레 이력 없음. 편의점 5분, 마트 7분."
        ),
        "facilities": ["분리형주방", "에어컨", "세탁기", "냉장고"],
        "transit": {"station": "뚝섬역", "walk_min": 8},
        "lat": 37.5477,
        "lng": 127.0468,
        "commute_legs": [
            {"type": "walk", "label": "집 → 뚝섬역", "minutes": 8},
            {"type": "subway", "label": "뚝섬역 → 강남역 (2호선)", "minutes": 20},
        ],
        "commute_total_minutes": 28,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "정보 없음", "pass": False},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "2층 남향", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 5, "icon": "store"},
            {"name": "마트", "walk_min": 7, "icon": "shopping-cart"},
        ],
    },
    # ── 영등포구 (강남역 25-32분) ──────────────────────────────────────────
    {
        "id": "P012",
        "type": "원룸",
        "title": "영등포역 원룸 3층",
        "deposit": 500,
        "monthly_rent": 55,
        "location": "서울 영등포구 영등포동",
        "address_detail": "영등포역 7번 출구 도보 8분",
        "description": (
            "3층 원룸, 교통 편리한 영등포. "
            "에어컨·세탁기·냉장고 포함. "
            "CCTV 설치. 곰팡이 없음. "
            "편의점·마트·약국 도보 5분 이내."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "영등포역", "walk_min": 8},
        "lat": 37.5157,
        "lng": 126.9069,
        "commute_legs": [
            {"type": "walk", "label": "집 → 영등포역", "minutes": 8},
            {"type": "subway", "label": "영등포역 → 신도림역 → 강남역 (1호선·2호선 환승)", "minutes": 24},
        ],
        "commute_total_minutes": 32,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "3층 일반 채광", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·마트 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 3, "icon": "store"},
            {"name": "마트", "walk_min": 5, "icon": "shopping-cart"},
            {"name": "약국", "walk_min": 4, "icon": "pill"},
        ],
    },
    # ── 광진구 (강남역 28-35분) ────────────────────────────────────────────
    {
        "id": "P013",
        "type": "오피스텔",
        "title": "건대입구역 오피스텔 9층",
        "deposit": 1500,
        "monthly_rent": 72,
        "location": "서울 광진구 화양동",
        "address_detail": "건대입구역 2번 출구 도보 4분",
        "description": (
            "9층 오피스텔, 건대 상권 인근. "
            "에어컨·세탁기·냉장고 포함. "
            "CCTV 24시간 운영. 반지하 아님. "
            "편의점·카페·음식점 도보 3분 이내. "
            "벌레·곰팡이 없음."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "건대입구역", "walk_min": 4},
        "lat": 37.5400,
        "lng": 127.0702,
        "commute_legs": [
            {"type": "walk", "label": "집 → 건대입구역", "minutes": 4},
            {"type": "subway", "label": "건대입구역 → 강남역 (2호선)", "minutes": 26},
        ],
        "commute_total_minutes": 30,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "24시간 CCTV 운영", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "9층 채광 우수", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·카페 도보 3분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 2, "icon": "store"},
            {"name": "카페", "walk_min": 3, "icon": "coffee"},
            {"name": "마트", "walk_min": 6, "icon": "shopping-cart"},
            {"name": "약국", "walk_min": 5, "icon": "pill"},
        ],
    },
    {
        "id": "P014",
        "type": "원룸",
        "title": "천호역 역세권 원룸 4층",
        "deposit": 500,
        "monthly_rent": 58,
        "location": "서울 강동구 천호동",
        "address_detail": "천호역 4번 출구 도보 7분",
        "description": (
            "4층 원룸, 남향 채광 좋음. "
            "에어컨·세탁기·냉장고 포함. "
            "건물 CCTV 설치. 곰팡이·벌레 없음. "
            "편의점 4분, 마트 6분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "천호역", "walk_min": 7},
        "lat": 37.5384,
        "lng": 127.1238,
        "commute_legs": [
            {"type": "walk", "label": "집 → 천호역", "minutes": 7},
            {"type": "subway", "label": "천호역 → 강남역 (5호선·2호선 환승)", "minutes": 25},
        ],
        "commute_total_minutes": 32,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "4층 남향", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 4분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 4, "icon": "store"},
            {"name": "마트", "walk_min": 6, "icon": "shopping-cart"},
        ],
    },
    # ── 용산구 (강남역 22-28분) ────────────────────────────────────────────
    {
        "id": "P015",
        "type": "오피스텔",
        "title": "이태원역 오피스텔 6층",
        "deposit": 2000,
        "monthly_rent": 78,
        "location": "서울 용산구 이태원동",
        "address_detail": "이태원역 2번 출구 도보 5분",
        "description": (
            "글로벌 분위기의 이태원 6층 오피스텔. "
            "에어컨·세탁기·냉장고 포함. "
            "CCTV 설치, 24시간 경비. "
            "편의점·카페·음식점 다수 도보 5분 이내. "
            "벌레·곰팡이 이력 없음."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "이태원역", "walk_min": 5},
        "lat": 37.5340,
        "lng": 126.9947,
        "commute_legs": [
            {"type": "walk", "label": "집 → 이태원역", "minutes": 5},
            {"type": "subway", "label": "이태원역 → 한강진역 → 강남역 (6호선·2호선 환승)", "minutes": 20},
        ],
        "commute_total_minutes": 25,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "24시간 경비·CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "6층 채광 우수", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·카페 다수", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 2, "icon": "store"},
            {"name": "카페", "walk_min": 3, "icon": "coffee"},
            {"name": "약국", "walk_min": 5, "icon": "pill"},
        ],
    },
    # ── 마포구 (강남역 30-38분) ────────────────────────────────────────────
    {
        "id": "P016",
        "type": "원룸",
        "title": "홍대입구역 원룸 3층",
        "deposit": 500,
        "monthly_rent": 62,
        "location": "서울 마포구 서교동",
        "address_detail": "홍대입구역 9번 출구 도보 7분",
        "description": (
            "홍대 문화 상권 인근 3층 원룸. "
            "에어컨·세탁기·냉장고 포함. "
            "건물 CCTV 설치. 반지하 아님. "
            "벌레·곰팡이 이력 없음. "
            "편의점·카페·마트 도보 5분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "홍대입구역", "walk_min": 7},
        "lat": 37.5573,
        "lng": 126.9248,
        "commute_legs": [
            {"type": "walk", "label": "집 → 홍대입구역", "minutes": 7},
            {"type": "subway", "label": "홍대입구역 → 합정역 → 강남역 (2호선)", "minutes": 30},
        ],
        "commute_total_minutes": 37,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "3층 채광 양호", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·카페 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 3, "icon": "store"},
            {"name": "마트", "walk_min": 5, "icon": "shopping-cart"},
            {"name": "카페", "walk_min": 2, "icon": "coffee"},
        ],
    },
    {
        "id": "P017",
        "type": "빌라",
        "title": "합정역 분리형 빌라 2층",
        "deposit": 700,
        "monthly_rent": 57,
        "location": "서울 마포구 합정동",
        "address_detail": "합정역 3번 출구 도보 8분",
        "description": (
            "분리형 구조의 합정동 빌라 2층. "
            "에어컨·세탁기·냉장고 포함. "
            "벌레·곰팡이 없는 쾌적한 환경. "
            "편의점 5분, 마트 7분, 카페 3분."
        ),
        "facilities": ["분리형주방", "에어컨", "세탁기", "냉장고"],
        "transit": {"station": "합정역", "walk_min": 8},
        "lat": 37.5497,
        "lng": 126.9143,
        "commute_legs": [
            {"type": "walk", "label": "집 → 합정역", "minutes": 8},
            {"type": "subway", "label": "합정역 → 강남역 (2호선·6호선 환승)", "minutes": 28},
        ],
        "commute_total_minutes": 36,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "정보 없음", "pass": False},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "2층 일반 채광", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 5, "icon": "store"},
            {"name": "마트", "walk_min": 7, "icon": "shopping-cart"},
            {"name": "카페", "walk_min": 3, "icon": "coffee"},
        ],
    },
    # ── 관악구 (강남역 35-42분) ────────────────────────────────────────────
    {
        "id": "P018",
        "type": "원룸",
        "title": "서울대입구역 원룸 3층",
        "deposit": 300,
        "monthly_rent": 50,
        "location": "서울 관악구 봉천동",
        "address_detail": "서울대입구역 3번 출구 도보 8분",
        "description": (
            "3층 원룸, 조용한 주택가. "
            "에어컨·세탁기·냉장고 포함. "
            "CCTV 설치. 반지하 아님. "
            "벌레·곰팡이 없음. 편의점 5분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "서울대입구역", "walk_min": 8},
        "lat": 37.4811,
        "lng": 126.9527,
        "commute_legs": [
            {"type": "walk", "label": "집 → 서울대입구역", "minutes": 8},
            {"type": "subway", "label": "서울대입구역 → 강남역 (2호선)", "minutes": 28},
        ],
        "commute_total_minutes": 36,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "3층 일반 채광", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 5, "icon": "store"},
            {"name": "마트", "walk_min": 8, "icon": "shopping-cart"},
        ],
    },
    {
        "id": "P019",
        "type": "빌라",
        "title": "신림역 빌라 2층",
        "deposit": 300,
        "monthly_rent": 45,
        "location": "서울 관악구 신림동",
        "address_detail": "신림역 4번 출구 도보 10분",
        "description": (
            "신림역 인근 저렴한 빌라 2층. "
            "에어컨·세탁기 포함. 냉장고 있음. "
            "반지하 아님. 벌레 없음. "
            "편의점·마트 도보 5분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고"],
        "transit": {"station": "신림역", "walk_min": 10},
        "lat": 37.4843,
        "lng": 126.9294,
        "commute_legs": [
            {"type": "walk", "label": "집 → 신림역", "minutes": 10},
            {"type": "subway", "label": "신림역 → 강남역 (2호선)", "minutes": 30},
        ],
        "commute_total_minutes": 40,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "정보 없음", "pass": False},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "2층 일반 채광", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·마트 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 4, "icon": "store"},
            {"name": "마트", "walk_min": 5, "icon": "shopping-cart"},
        ],
    },
    # ── 은평구 / 종로구 / 강북구 (강남역 38-50분) ─────────────────────────
    {
        "id": "P020",
        "type": "원룸",
        "title": "불광역 원룸 4층",
        "deposit": 300,
        "monthly_rent": 47,
        "location": "서울 은평구 불광동",
        "address_detail": "불광역 1번 출구 도보 6분",
        "description": (
            "4층 남향 원룸, 채광 양호. "
            "에어컨·세탁기·냉장고 포함. "
            "CCTV 설치, 곰팡이 없음. "
            "편의점 4분, 마트 8분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "불광역", "walk_min": 6},
        "lat": 37.6094,
        "lng": 126.9296,
        "commute_legs": [
            {"type": "walk", "label": "집 → 불광역", "minutes": 6},
            {"type": "subway", "label": "불광역 → 연신내역 → 강남역 (3호선·6호선 환승)", "minutes": 38},
        ],
        "commute_total_minutes": 44,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "4층 남향", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 4분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 4, "icon": "store"},
            {"name": "마트", "walk_min": 8, "icon": "shopping-cart"},
        ],
    },
    {
        "id": "P021",
        "type": "원룸",
        "title": "혜화역 원룸 3층",
        "deposit": 500,
        "monthly_rent": 55,
        "location": "서울 종로구 혜화동",
        "address_detail": "혜화역 4번 출구 도보 7분",
        "description": (
            "대학로 인근 문화적 환경의 3층 원룸. "
            "에어컨·세탁기·냉장고 포함. "
            "건물 CCTV 설치. 반지하 아님. "
            "곰팡이·벌레 없음. 편의점·카페 도보 5분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "혜화역", "walk_min": 7},
        "lat": 37.5823,
        "lng": 127.0021,
        "commute_legs": [
            {"type": "walk", "label": "집 → 혜화역", "minutes": 7},
            {"type": "subway", "label": "혜화역 → 동대문역 → 강남역 (4호선·2호선 환승)", "minutes": 35},
        ],
        "commute_total_minutes": 42,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "3층 일반 채광", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·카페 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 4, "icon": "store"},
            {"name": "카페", "walk_min": 5, "icon": "coffee"},
            {"name": "약국", "walk_min": 6, "icon": "pill"},
        ],
    },
    {
        "id": "P022",
        "type": "빌라",
        "title": "미아사거리역 저가 빌라 1층",
        "deposit": 200,
        "monthly_rent": 40,
        "location": "서울 강북구 미아동",
        "address_detail": "미아사거리역 3번 출구 도보 10분",
        "description": (
            "강북구 저렴한 빌라. "
            "에어컨·세탁기 포함. 냉장고 있음. "
            "1층으로 채광 다소 부족. 반지하 아님. "
            "편의점 5분, 마트 8분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고"],
        "transit": {"station": "미아사거리역", "walk_min": 10},
        "lat": 37.6132,
        "lng": 127.0290,
        "commute_legs": [
            {"type": "walk", "label": "집 → 미아사거리역", "minutes": 10},
            {"type": "subway", "label": "미아사거리역 → 강남역 (4호선·2호선 환승)", "minutes": 42},
        ],
        "commute_total_minutes": 52,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "정보 없음", "pass": False},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "1층, 채광 다소 부족", "pass": False},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 5, "icon": "store"},
            {"name": "마트", "walk_min": 8, "icon": "shopping-cart"},
        ],
    },
    {
        "id": "P023",
        "type": "빌라",
        "title": "노원역 대형 빌라 3층",
        "deposit": 500,
        "monthly_rent": 42,
        "location": "서울 노원구 상계동",
        "address_detail": "노원역 1번 출구 도보 8분",
        "description": (
            "노원 저렴한 대형 빌라 3층. "
            "에어컨·세탁기·냉장고 포함. "
            "건물 CCTV. 반지하 아님. "
            "벌레·곰팡이 없음. 편의점·마트 도보 5분."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "노원역", "walk_min": 8},
        "lat": 37.6555,
        "lng": 127.0568,
        "commute_legs": [
            {"type": "walk", "label": "집 → 노원역", "minutes": 8},
            {"type": "subway", "label": "노원역 → 강남역 (7호선·2호선 환승)", "minutes": 45},
        ],
        "commute_total_minutes": 53,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "건물 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "3층 일반 채광", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·마트 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 4, "icon": "store"},
            {"name": "마트", "walk_min": 5, "icon": "shopping-cart"},
            {"name": "약국", "walk_min": 7, "icon": "pill"},
        ],
    },
    # ── 추가 매물 (다양성 확보) ────────────────────────────────────────────
    {
        "id": "P024",
        "type": "오피스텔",
        "title": "한강진역 한강뷰 오피스텔 15층",
        "deposit": 3000,
        "monthly_rent": 110,
        "location": "서울 용산구 한남동",
        "address_detail": "한강진역 1번 출구 도보 6분",
        "description": (
            "15층 한강뷰 오피스텔, 최고급 사양. "
            "풀옵션(에어컨, 세탁기, 냉장고, 식기세척기, 인덕션) 포함. "
            "24시간 경비·CCTV, 헬스장 구비. "
            "편의점·카페·마트 도보 5분. "
            "벌레·곰팡이 이력 없음."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "식기세척기", "인덕션", "CCTV", "헬스장"],
        "transit": {"station": "한강진역", "walk_min": 6},
        "lat": 37.5397,
        "lng": 127.0052,
        "commute_legs": [
            {"type": "walk", "label": "집 → 한강진역", "minutes": 6},
            {"type": "subway", "label": "한강진역 → 이태원역 → 강남역 (6호선·2호선 환승)", "minutes": 20},
        ],
        "commute_total_minutes": 26,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "24시간 경비·전층 CCTV", "pass": True},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "15층 한강뷰 최고 조망", "pass": True},
            {"icon": "store", "label": "편의시설 근접", "detail": "편의점·카페 도보 5분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 3, "icon": "store"},
            {"name": "마트", "walk_min": 5, "icon": "shopping-cart"},
            {"name": "카페", "walk_min": 4, "icon": "coffee"},
            {"name": "헬스장", "walk_min": 0, "icon": "dumbbell"},
        ],
    },
    {
        "id": "P025",
        "type": "원룸",
        "title": "강남역 초역세권 반지하 원룸",
        "deposit": 200,
        "monthly_rent": 55,
        "location": "서울 강남구 역삼동",
        "address_detail": "강남역 10번 출구 도보 3분",
        "description": (
            "강남역 도보 3분 초역세권. "
            "에어컨·세탁기 포함. 냉장고 있음. "
            "반지하 구조로 채광 제한. "
            "과거 습기 이력 있으나 현재 제습기 설치 완료."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고"],
        "transit": {"station": "강남역", "walk_min": 3},
        "lat": 37.4990,
        "lng": 127.0280,
        "commute_legs": [
            {"type": "walk", "label": "집 → 강남역", "minutes": 3},
        ],
        "commute_total_minutes": 3,
        "is_basement": True,
        "night_safety": [
            {"icon": "camera", "label": "CCTV 설치", "detail": "정보 없음", "pass": False},
            {"icon": "sun", "label": "채광/층수 양호", "detail": "반지하 채광 제한", "pass": False},
            {"icon": "store", "label": "편의시설 근접", "detail": "강남역 상권 도보 3분", "pass": True},
        ],
        "convenience": [
            {"name": "편의점", "walk_min": 2, "icon": "store"},
            {"name": "마트", "walk_min": 4, "icon": "shopping-cart"},
            {"name": "카페", "walk_min": 2, "icon": "coffee"},
        ],
    },
]

_SOFT_WEIGHTS = {
    "pests": 25,
    "mold": 25,
    "default_options": 20,
    "convenience_facilities": 15,
    "extra_notes": 15,
}

_FACILITY_ALIASES: dict[str, list[str]] = {
    "편의점": ["편의점"],
    "마트": ["마트", "슈퍼"],
    "병원": ["병원", "의원"],
    "약국": ["약국"],
    "카페": ["카페", "커피"],
    "세탁소": ["세탁소"],
    "헬스장": ["헬스장", "피트니스"],
}

_PEST_CLEAR = ["벌레 이력 없", "벌레 민원 없", "벌레 걱정 없", "해충 없", "벌레·곰팡이 없", "벌레·곰팡이 이력 없"]
_PEST_BAD = ["벌레", "바퀴", "해충"]
_MOLD_CLEAR = ["곰팡이 없", "곰팡이 이력 없", "도배·장판 교체", "도배 완료", "결로 없", "벌레·곰팡이 없"]
_MOLD_BAD = ["곰팡이", "결로"]
_MOLD_PARTIAL = ["습기"]


def _apply_hard_filter(
    properties: list[dict[str, Any]],
    conditions: ConditionState,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    max_rent: int | None = conditions["hard_conditions"]["monthly_rent"].get("max_manwon")
    avoid_basement: bool | None = conditions["soft_conditions"]["basement"].get("avoid")
    max_commute: int | None = conditions["hard_conditions"]["location_transport"].get("commute_time_max_minutes")

    passed: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for prop in properties:
        fail_reason: str | None = None

        if max_rent is not None and prop["monthly_rent"] > max_rent:
            fail_reason = f"월세 {prop['monthly_rent']}만원 > 상한 {max_rent}만원"
        elif avoid_basement is True and prop.get("is_basement", False):
            fail_reason = "반지하 매물 (사용자 제외 요청)"
        elif max_commute is not None and prop.get("commute_total_minutes", prop["transit"]["walk_min"]) > max_commute:
            fail_reason = f"출퇴근 {prop.get('commute_total_minutes', prop['transit']['walk_min'])}분 > 상한 {max_commute}분"

        if fail_reason:
            failed.append({"property": prop, "reason": fail_reason})
        else:
            passed.append(prop)

    return passed, failed


def _score_rule(
    prop: dict[str, Any],
    soft: dict[str, Any],
) -> tuple[int, list[dict[str, Any]]]:
    desc = prop["description"]
    fac_str = " ".join(prop["facilities"])
    combined = desc + " " + fac_str

    score = 0
    card_matches: list[dict[str, Any]] = []

    # pests (25점)
    weight = _SOFT_WEIGHTS["pests"]
    if soft["pests"].get("avoid"):
        if any(kw in combined for kw in _PEST_CLEAR):
            pts, matched, evidence = weight, True, "설명에서 벌레 없음 확인"
        elif any(kw in combined for kw in _PEST_BAD):
            pts, matched, evidence = 0, False, "벌레/해충 관련 언급 있음"
        else:
            pts, matched, evidence = weight // 2, "partial", "벌레 관련 정보 없음 (중립)"
    else:
        pts, matched, evidence = weight, True, "조건 없음"
    score += pts
    card_matches.append({"card": "pests", "matched": matched, "evidence": evidence})

    # mold (25점)
    weight = _SOFT_WEIGHTS["mold"]
    if soft["mold"].get("avoid"):
        if any(kw in combined for kw in _MOLD_CLEAR):
            pts, matched, evidence = weight, True, "설명에서 곰팡이 없음 확인"
        elif any(kw in combined for kw in _MOLD_BAD):
            pts, matched, evidence = 0, False, "곰팡이/결로 관련 언급 있음"
        elif any(kw in combined for kw in _MOLD_PARTIAL):
            pts, matched, evidence = weight // 2, "partial", "습기 언급 있음"
        else:
            pts, matched, evidence = weight // 2, "partial", "곰팡이 관련 정보 없음 (중립)"
    else:
        pts, matched, evidence = weight, True, "조건 없음"
    score += pts
    card_matches.append({"card": "mold", "matched": matched, "evidence": evidence})

    # default_options (20점)
    weight = _SOFT_WEIGHTS["default_options"]
    wanted = list({*soft["default_options"].get("preferred", []), *soft["default_options"].get("required", [])})
    if wanted:
        matched_opts = [opt for opt in wanted if opt in fac_str or opt in desc]
        ratio = len(matched_opts) / len(wanted)
        pts = round(ratio * weight)
        matched = ratio >= 0.8
        evidence = f"{len(matched_opts)}/{len(wanted)} 항목 포함: {', '.join(matched_opts) or '없음'}"
    else:
        pts, matched, evidence = weight, True, "조건 없음"
    score += pts
    card_matches.append({"card": "default_options", "matched": matched, "evidence": evidence})

    # convenience_facilities (15점)
    weight = _SOFT_WEIGHTS["convenience_facilities"]
    wanted_fac = list({
        *soft["convenience_facilities"].get("preferred", []),
        *soft["convenience_facilities"].get("required", []),
    })
    if wanted_fac:
        matched_fac = [
            fac for fac in wanted_fac
            if any(alias in combined for alias in _FACILITY_ALIASES.get(fac, [fac]))
        ]
        ratio = len(matched_fac) / len(wanted_fac)
        pts = round(ratio * weight)
        matched = ratio >= 0.7
        evidence = f"편의시설 {len(matched_fac)}/{len(wanted_fac)} 확인: {', '.join(matched_fac) or '없음'}"
    else:
        pts, matched, evidence = weight, True, "조건 없음"
    score += pts
    card_matches.append({"card": "convenience_facilities", "matched": matched, "evidence": evidence})

    # extra_notes (15점)
    weight = _SOFT_WEIGHTS["extra_notes"]
    extra_notes: list[str] = soft.get("extra_notes", [])
    if extra_notes:
        note_text = " ".join(extra_notes)
        note_words = {w for w in re.findall(r"[가-힣]{2,}", note_text)}
        desc_words = {w for w in re.findall(r"[가-힣]{2,}", combined)}
        overlap = note_words & desc_words
        if len(overlap) >= 2:
            pts, matched, evidence = weight, True, f"키워드 매칭: {', '.join(list(overlap)[:3])}"
        elif len(overlap) == 1:
            pts, matched, evidence = weight // 2, "partial", f"키워드 부분 매칭: {list(overlap)[0]}"
        else:
            pts, matched, evidence = 0, False, "추가 요구사항 키워드 미발견"
    else:
        pts, matched, evidence = weight, True, "추가 요구사항 없음"
    score += pts
    card_matches.append({"card": "extra_notes", "matched": matched, "evidence": evidence})

    return score, card_matches


_CURATOR_SYSTEM_PROMPT = """
너는 부동산 매물 평가 전문가다. 소프트 조건 카드와 매물 설명을 읽고 각 카드 충족 여부를 JSON으로만 반환한다.
추가 설명 없이 JSON 객체만 반환한다.

출력 형태:
{
  "pests": {"matched": true, "evidence": "근거 한 문장"},
  "mold": {"matched": true, "evidence": "근거 한 문장"},
  "default_options": {"matched": true, "evidence": "근거 한 문장"},
  "convenience_facilities": {"matched": "partial", "evidence": "근거 한 문장"},
  "extra_notes": {"matched": false, "evidence": "근거 한 문장"}
}

규칙:
- matched=true: 설명·시설에서 명확히 충족 확인
- matched="partial": 일부 충족 또는 정보 불명확
- matched=false: 미충족 또는 부정적 언급
- evidence: 매물 설명 직접 인용 또는 "정보 없음"
- pests.avoid=true일 때: 벌레/해충 부정적 언급 없고 "벌레 없음" 등 긍정 표현이 있으면 true
- mold.avoid=true일 때: 곰팡이/습기/결로 언급 없이 "곰팡이 없음/도배 완료" 등이 있으면 true
- default_options: preferred/required 항목이 facilities 또는 설명에 포함되면 true
- convenience_facilities: preferred/required 편의시설이 설명에 언급되면 true
- extra_notes가 없으면 모든 카드를 true로 반환
""".strip()


def _parse_curator_json(content: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        stripped = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        parsed, _ = decoder.raw_decode(stripped.strip())
    except json.JSONDecodeError as exc:
        raise SolarClientError(f"Curator LLM returned non-JSON: {content}") from exc
    if not isinstance(parsed, dict) or "pests" not in parsed:
        raise SolarClientError(f"Curator LLM returned unexpected shape: {parsed}")
    return parsed


def _score_from_llm_output(
    llm_result: dict[str, Any],
) -> tuple[int, list[dict[str, Any]]]:
    score = 0
    card_matches: list[dict[str, Any]] = []
    for card, weight in _SOFT_WEIGHTS.items():
        item = llm_result.get(card, {})
        matched = item.get("matched", False)
        evidence = item.get("evidence", "정보 없음")
        if matched is True:
            pts = weight
        elif matched == "partial":
            pts = weight // 2
        else:
            pts = 0
        score += pts
        card_matches.append({"card": card, "matched": matched, "evidence": evidence})
    return score, card_matches


def _score_solar(
    prop: dict[str, Any],
    conditions: ConditionState,
    api_key: str | None,
) -> tuple[int, list[dict[str, Any]], str]:
    soft = conditions["soft_conditions"]
    user_message = json.dumps(
        {
            "soft_conditions": soft,
            "property": {
                "id": prop["id"],
                "facilities": prop["facilities"],
                "description": prop["description"],
            },
        },
        ensure_ascii=False,
    )
    messages = [
        {"role": "system", "content": _CURATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    content = call_upstage_chat_content(messages=messages, api_key=api_key)
    llm_result = _parse_curator_json(content)
    score, card_matches = _score_from_llm_output(llm_result)
    return score, card_matches, "solar"


def _build_result(
    prop: dict[str, Any],
    score: int,
    card_matches: list[dict[str, Any]],
    agent_mode: str,
) -> dict[str, Any]:
    return {
        "property_id": prop["id"],
        "title": prop["title"],
        "type": prop["type"],
        "score": score,
        "hard_filter_passed": True,
        "deposit": prop["deposit"],
        "monthly_rent": prop["monthly_rent"],
        "location": prop["location"],
        "address_detail": prop["address_detail"],
        "description": prop["description"],
        "facilities": prop["facilities"],
        "transit_walk_min": prop["transit"]["walk_min"],
        "transit_station": prop["transit"]["station"],
        "soft_card_matches": card_matches,
        "agent_mode": agent_mode,
        # 구조화된 입지 분석 필드
        "lat": prop.get("lat"),
        "lng": prop.get("lng"),
        "commute_legs": prop.get("commute_legs", []),
        "commute_total_minutes": prop.get("commute_total_minutes", prop["transit"]["walk_min"]),
        "night_safety": prop.get("night_safety", []),
        "convenience": prop.get("convenience", []),
    }


class ListingCurator:
    def __init__(self, *, use_solar: bool = True, api_key: str | None = None) -> None:
        self.use_solar = use_solar
        self.api_key = api_key

    def recommend(
        self,
        conditions: ConditionState,
        session_id: str = "default",
        top_n: int = 3,
    ) -> dict[str, Any]:
        passed, _ = _apply_hard_filter(MOCK_PROPERTIES, conditions)
        soft = conditions["soft_conditions"]
        scored: list[dict[str, Any]] = []

        for prop in passed:
            if self.use_solar and (self.api_key or get_solar_api_key()):
                try:
                    score, card_matches, agent_mode = _score_solar(prop, conditions, self.api_key)
                except SolarClientError:
                    score, card_matches = _score_rule(prop, soft)
                    agent_mode = "rule_fallback"
            else:
                score, card_matches = _score_rule(prop, soft)
                agent_mode = "rule"

            scored.append(_build_result(prop, score, card_matches, agent_mode))

        top = sorted(scored, key=lambda x: x["score"], reverse=True)[:top_n]
        return {"session_id": session_id, "top_properties": top}
