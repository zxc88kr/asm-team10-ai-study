from __future__ import annotations

import re
from copy import deepcopy

from .schema import ConditionState, merge_unique, update_missing_and_question


AREA_KEYWORDS = [
    "강남",
    "홍대",
    "신촌",
    "성수",
    "건대",
    "잠실",
    "왕십리",
    "혜화",
    "서울대입구",
    "낙성대",
    "사당",
    "신림",
]

FACILITY_KEYWORDS = ["편의점", "마트", "병원", "약국", "카페", "세탁소", "헬스장", "공원"]
OPTION_KEYWORDS = ["에어컨", "냉장고", "세탁기", "침대", "책상", "옷장", "인덕션", "전자레인지", "와이파이"]
PEST_KEYWORDS = ["벌레", "바퀴", "바퀴벌레", "해충"]
MOLD_KEYWORDS = ["곰팡이", "습기", "결로"]


def _find_keywords(text: str, keywords: list[str]) -> list[str]:
    return [keyword for keyword in keywords if keyword in text]


def _generic_facility_intent(text: str) -> bool:
    return bool(re.search(r"편의\s*시설|편의시설|주변에\s*많", text))


def _station_names(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"[가-힣A-Za-z0-9]+역", text)))


def _monthly_rent_manwon(text: str) -> int | None:
    if not re.search(r"월세|월\s|관리비|고정비|예산|만원|만 원", text):
        return None
    match = re.search(r"(\d+)\s*만\s*원?", text)
    return int(match.group(1)) if match else None


def _commute_minutes(text: str) -> int | None:
    if not re.search(r"출퇴근|통근|교통|거리|이내|역세권|도보", text):
        return None
    match = re.search(r"(\d+)\s*분", text)
    return int(match.group(1)) if match else None


def _avoid_intent(text: str) -> bool:
    return bool(re.search(r"싫|피하고|제외|없었|없으면|안 나왔|안나왔|걱정|문제|무서", text))


def _required_intent(text: str) -> bool:
    return bool(re.search(r"필수|꼭|반드시|있어야|가까워야|원해", text))


def _no_more_soft_intent(text: str) -> bool:
    return bool(re.search(r"^(그리곤\s*)?(더\s*)?(없어|없어요|없습니다)$|그 외엔 없어|그 외에는 없어", text))


def apply_rule_extraction(state: ConditionState, user_message: str) -> ConditionState:
    text = user_message.strip()
    next_state = deepcopy(state)

    hard = next_state["hard_conditions"]
    location = hard["location_transport"]
    rent = hard["monthly_rent"]
    soft = next_state["soft_conditions"]

    areas = _find_keywords(text, AREA_KEYWORDS)
    stations = _station_names(text)
    location["areas"] = merge_unique(location["areas"], areas)
    location["landmarks"] = merge_unique(location["landmarks"], stations)

    commute_minutes = _commute_minutes(text)
    if commute_minutes is not None:
        location["commute_time_max_minutes"] = commute_minutes

    if re.search(r"출퇴근|통근|교통|역세권|도보|버스|지하철|회사|학교", text):
        location["transport_notes"] = merge_unique(location["transport_notes"], [text])

    rent_manwon = _monthly_rent_manwon(text)
    if rent_manwon is not None:
        rent["max_manwon"] = rent_manwon
        rent["max_krw"] = rent_manwon * 10000

    if re.search(r"관리비\s*포함|포함해서|고정비", text):
        rent["includes_management_fee"] = True

    facilities = _find_keywords(text, FACILITY_KEYWORDS)
    if _generic_facility_intent(text):
        facilities = merge_unique(facilities, ["편의 시설"])

    if facilities:
        target = "required" if _required_intent(text) else "preferred"
        soft["convenience_facilities"][target] = merge_unique(soft["convenience_facilities"][target], facilities)
        soft["convenience_facilities"]["notes"] = merge_unique(soft["convenience_facilities"]["notes"], [text])

    options = _find_keywords(text, OPTION_KEYWORDS)
    if options:
        target = "required" if _required_intent(text) else "preferred"
        soft["default_options"][target] = merge_unique(soft["default_options"][target], options)

    if _find_keywords(text, PEST_KEYWORDS):
        soft["pests"]["avoid"] = True if _avoid_intent(text) else soft["pests"]["avoid"]
        soft["pests"]["evidence"] = merge_unique(soft["pests"]["evidence"], [text])

    if _find_keywords(text, MOLD_KEYWORDS):
        soft["mold"]["avoid"] = True if _avoid_intent(text) else soft["mold"]["avoid"]
        soft["mold"]["evidence"] = merge_unique(soft["mold"]["evidence"], [text])

    if "반지하" in text:
        soft["basement"]["avoid"] = True if _avoid_intent(text) else soft["basement"]["avoid"]
        soft["basement"]["evidence"] = merge_unique(soft["basement"]["evidence"], [text])

    known_signal = any(
        [
            areas,
            stations,
            commute_minutes is not None,
            rent_manwon is not None,
            facilities,
            _generic_facility_intent(text),
            options,
            _find_keywords(text, PEST_KEYWORDS),
            _find_keywords(text, MOLD_KEYWORDS),
            "반지하" in text,
        ]
    )
    if text and (not known_signal or _no_more_soft_intent(text)):
        soft["extra_notes"] = merge_unique(soft["extra_notes"], [text])

    return update_missing_and_question(next_state)
