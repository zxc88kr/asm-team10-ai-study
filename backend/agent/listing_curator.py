from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from .schema import ConditionState
from .solar_client import SolarClientError, call_upstage_chat_content, get_solar_api_key


MOCK_PROPERTIES: list[dict[str, Any]] = [
    {
        "id": "P001",
        "type": "빌라",
        "title": "장전동 복층빌라 2층",
        "deposit": 1000,
        "monthly_rent": 65,
        "location": "부산 금정구 장전동",
        "address_detail": "부산대역 도보 7분",
        "description": (
            "복층 구조로 채광이 뛰어나고 통풍이 잘 됩니다. "
            "분리형 주방이 갖춰져 있어 요리 냄새 걱정이 없습니다. "
            "2층이라 반지하가 아니며 벌레 이력 없음. "
            "에어컨, 세탁기, 냉장고 기본 포함. 건물 입구 CCTV 설치."
        ),
        "facilities": ["분리형주방", "복층", "에어컨", "세탁기", "냉장고", "CCTV"],
        "transit": {"station": "부산대역", "walk_min": 7},
    },
    {
        "id": "P002",
        "type": "원룸",
        "title": "장전동 역세권 원룸 301호",
        "deposit": 500,
        "monthly_rent": 45,
        "location": "부산 금정구 장전동",
        "address_detail": "부산대역 도보 4분, 편의점 1분 거리",
        "description": (
            "역에서 4분 거리로 교통이 편리합니다. "
            "건물 앞 편의점, 마트 5분. 3층 원룸으로 햇볕이 잘 듭니다. "
            "세탁기, 에어컨 구비. 최근 도배·장판 교체 완료, 곰팡이 없음."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고"],
        "transit": {"station": "부산대역", "walk_min": 4},
    },
    {
        "id": "P003",
        "type": "오피스텔",
        "title": "부곡동 신축 오피스텔 505호",
        "deposit": 1000,
        "monthly_rent": 80,
        "location": "부산 금정구 부곡동",
        "address_detail": "온천장역 도보 6분",
        "description": (
            "2024년 신축으로 내부가 깨끗합니다. "
            "풀옵션(에어컨, 세탁기, 냉장고, 전자레인지, 인덕션) 포함. "
            "5층이라 조망 좋고 벌레·곰팡이 이력 없음. 건물 내 편의점 입점."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고", "전자레인지", "인덕션"],
        "transit": {"station": "온천장역", "walk_min": 6},
    },
    {
        "id": "P004",
        "type": "원룸",
        "title": "장전동 반지하 원룸 B01호",
        "deposit": 300,
        "monthly_rent": 35,
        "location": "부산 금정구 장전동",
        "address_detail": "부산대역 도보 10분",
        "description": (
            "보증금·월세가 매우 저렴합니다. "
            "반지하 구조로 습기가 있을 수 있습니다. "
            "에어컨 없음, 세탁기 공용. "
            "과거 장마철 곰팡이 흔적 있었으나 현재 제거 완료."
        ),
        "facilities": ["냉장고"],
        "transit": {"station": "부산대역", "walk_min": 10},
        "is_basement": True,
    },
    {
        "id": "P005",
        "type": "빌라",
        "title": "대연동 남향 빌라 202호",
        "deposit": 700,
        "monthly_rent": 55,
        "location": "부산 남구 대연동",
        "address_detail": "경성대·부경대역 도보 8분, 편의점 3분",
        "description": (
            "남향 2층으로 햇볕이 잘 들고 환기가 좋습니다. "
            "편의점, 카페, 약국 근접. "
            "에어컨, 세탁기, 냉장고 포함. "
            "벌레 민원 이력 없는 쾌적한 환경."
        ),
        "facilities": ["에어컨", "세탁기", "냉장고"],
        "transit": {"station": "경성대·부경대역", "walk_min": 8},
    },
    {
        "id": "P006",
        "type": "원룸",
        "title": "대연동 저가 원룸 104호",
        "deposit": 200,
        "monthly_rent": 40,
        "location": "부산 남구 대연동",
        "address_detail": "경성대·부경대역 도보 12분",
        "description": (
            "월세가 가장 저렴한 옵션입니다. "
            "1층 구조로 채광이 다소 부족합니다. "
            "에어컨 없음, 세탁기 없음(공용). "
            "화장실 옆 습기 약간 있는 편."
        ),
        "facilities": ["냉장고"],
        "transit": {"station": "경성대·부경대역", "walk_min": 12},
    },
    {
        "id": "P007",
        "type": "빌라",
        "title": "부곡동 분리형 빌라 303호",
        "deposit": 1000,
        "monthly_rent": 70,
        "location": "부산 금정구 부곡동",
        "address_detail": "온천장역 도보 9분, 마트 5분",
        "description": (
            "분리형 구조로 방과 주방이 독립되어 요리 환경이 쾌적합니다. "
            "3층이라 채광이 좋고, 최근 리모델링 완료. "
            "에어컨, 세탁기 포함. 마트·편의점 근접. "
            "벌레·곰팡이 이력 없는 깨끗한 건물."
        ),
        "facilities": ["분리형주방", "에어컨", "세탁기", "냉장고"],
        "transit": {"station": "온천장역", "walk_min": 9},
    },
    {
        "id": "P008",
        "type": "원룸",
        "title": "장전동 옥탑 원룸 R01호",
        "deposit": 500,
        "monthly_rent": 48,
        "location": "부산 금정구 장전동",
        "address_detail": "부산대역 도보 15분",
        "description": (
            "옥탑방으로 탁 트인 조망과 채광이 뛰어납니다. "
            "독립 공간으로 프라이버시가 좋고 벌레 걱정이 없습니다. "
            "에어컨, 세탁기 포함. 편의점 도보 5분."
        ),
        "facilities": ["에어컨", "세탁기"],
        "transit": {"station": "부산대역", "walk_min": 15},
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

_PEST_CLEAR = ["벌레 이력 없", "벌레 민원 없", "벌레 걱정 없", "해충 없"]
_PEST_BAD = ["벌레", "바퀴", "해충"]
_MOLD_CLEAR = ["곰팡이 없", "곰팡이 이력 없", "도배·장판 교체", "도배 완료", "결로 없"]
_MOLD_BAD = ["곰팡이", "결로"]
_MOLD_PARTIAL = ["습기"]


def _apply_hard_filter(
    properties: list[dict[str, Any]],
    conditions: ConditionState,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    max_rent: int | None = conditions["hard_conditions"]["monthly_rent"].get("max_manwon")
    avoid_basement: bool | None = conditions["soft_conditions"]["basement"].get("avoid")

    passed: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for prop in properties:
        fail_reason: str | None = None

        if max_rent is not None and prop["monthly_rent"] > max_rent:
            fail_reason = f"월세 {prop['monthly_rent']}만원 > 상한 {max_rent}만원"
        elif avoid_basement is True and prop.get("is_basement", False):
            fail_reason = "반지하 매물 (사용자 제외 요청)"

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
