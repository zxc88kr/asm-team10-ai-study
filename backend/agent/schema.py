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
    "is_complete": False,
    "next_action": "ask_required_conditions",
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


def _has_soft_condition(state: ConditionState) -> bool:
    soft = state["soft_conditions"]
    facilities = soft["convenience_facilities"]
    options = soft["default_options"]

    return any(
        [
            facilities["required"],
            facilities["preferred"],
            facilities["notes"],
            soft["pests"]["avoid"] is not None,
            soft["pests"]["evidence"],
            options["required"],
            options["preferred"],
            soft["basement"]["avoid"] is not None,
            soft["basement"]["evidence"],
            soft["mold"]["avoid"] is not None,
            soft["mold"]["evidence"],
        ]
    )


def _has_no_more_soft_intent(state: ConditionState) -> bool:
    notes = state["soft_conditions"]["extra_notes"]
    return any(note in {"없어", "없어요", "더 없어", "더 없어요", "그리곤 없어", "그 외엔 없어"} for note in notes)


def update_missing_and_question(state: ConditionState, *, trust_llm_action: bool = False) -> ConditionState:
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

    # 하드 조건 누락 — LLM 판단과 무관하게 규칙 강제 (100% 명확한 분기)
    if "위치/교통" in missing:
        state["next_question"] = "어느 지역이나 역 기준으로 찾고 싶으세요? 출퇴근 제한 시간도 있으면 같이 알려주세요."
        state["is_complete"] = False
        state["next_action"] = "ask_required_conditions"
        return state

    if "월세" in missing:
        state["next_question"] = "월세는 최대 얼마까지 가능하세요? 관리비 포함 기준인지도 알려주세요."
        state["is_complete"] = False
        state["next_action"] = "ask_required_conditions"
        return state

    # 하드 조건 충족 이후 — LLM 판단 신뢰
    if trust_llm_action and state.get("next_action") in ("recommend_listings", "ask_soft_conditions"):
        if state["next_action"] == "recommend_listings":
            state["is_complete"] = True
            if not state.get("next_question"):
                state["next_question"] = "조건이 충분히 정리됐어요. 이 조건으로 매물을 추천해볼게요."
        else:
            state["is_complete"] = False
        return state

    # 폴백 — Solar 실패·규칙 추출 시 기존 규칙 사용
    if _has_soft_condition(state) or _has_no_more_soft_intent(state):
        state["next_question"] = "조건이 충분히 정리됐어요. 이 조건으로 매물을 추천해볼게요."
        state["is_complete"] = True
        state["next_action"] = "recommend_listings"
    else:
        state["next_question"] = "편의 시설, 벌레 여부, 기본 옵션, 반지하 여부, 곰팡이처럼 방 상태에서 중요한 조건이 있나요?"
        state["is_complete"] = False
        state["next_action"] = "ask_soft_conditions"

    return state
