from __future__ import annotations

from copy import deepcopy
from typing import Any


ConditionState = dict[str, Any]


EMPTY_CONDITIONS: ConditionState = {
    "hard_conditions": {
        "location_transport": {
            "areas": [],
            "landmarks": [],
            "commute_time_max_minutes": None,
            "transport_notes": [],
        },
        "monthly_rent": {
            "max_krw": None,
            "max_manwon": None,
            "includes_management_fee": None,
        },
    },
    "soft_conditions": {
        "convenience_facilities": {
            "required": [],
            "preferred": [],
            "notes": [],
        },
        "pests": {
            "avoid": None,
            "evidence": [],
        },
        "default_options": {
            "required": [],
            "preferred": [],
        },
        "basement": {
            "avoid": None,
            "evidence": [],
        },
        "mold": {
            "avoid": None,
            "evidence": [],
        },
        "extra_notes": [],
    },
    "missing_required_conditions": ["위치/교통", "월세"],
    "next_question": "어느 지역이나 역 기준으로 찾고 싶으세요? 출퇴근 제한 시간도 있으면 같이 알려주세요.",
}


def create_empty_conditions() -> ConditionState:
    return deepcopy(EMPTY_CONDITIONS)


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def merge_unique(existing: list[str], incoming: list[str]) -> list[str]:
    return unique([*existing, *incoming])


def update_missing_and_question(state: ConditionState) -> ConditionState:
    location = state["hard_conditions"]["location_transport"]
    rent = state["hard_conditions"]["monthly_rent"]

    missing: list[str] = []
    has_location = bool(location["areas"] or location["landmarks"] or location["commute_time_max_minutes"])
    has_rent = rent["max_manwon"] is not None

    if not has_location:
        missing.append("위치/교통")
    if not has_rent:
        missing.append("월세")

    state["missing_required_conditions"] = missing

    if "위치/교통" in missing:
        state["next_question"] = "어느 지역이나 역 기준으로 찾고 싶으세요? 출퇴근 제한 시간도 있으면 같이 알려주세요."
    elif "월세" in missing:
        state["next_question"] = "월세는 최대 얼마까지 가능하세요? 관리비 포함 기준인지도 알려주세요."
    else:
        state["next_question"] = "편의 시설, 벌레 여부, 기본 옵션, 반지하 여부, 곰팡이처럼 방 상태에서 중요한 조건이 있나요?"

    return state
