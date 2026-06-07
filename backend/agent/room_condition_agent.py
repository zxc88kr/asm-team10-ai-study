from __future__ import annotations

import json
from copy import deepcopy

from .rule_extractor import apply_rule_extraction
from .schema import ConditionState, create_empty_conditions, update_missing_and_question
from .solar_client import SolarClientError, call_upstage_json, get_solar_api_key


SYSTEM_PROMPT = """
너는 자취방 조건을 정리하는 부동산 조건 추출 agent다.
반드시 JSON 객체만 반환한다.
최상위 키는 반드시 hard_conditions, soft_conditions, missing_required_conditions, next_question, is_complete, next_action 만 사용한다.
current_state, user_message, required_output_shape 같은 wrapper 키를 반환하지 않는다.

분류 규칙:
- hard_conditions.location_transport: 위치/교통 조건. 지역, 역, 출퇴근 시간, 도보/지하철/버스 조건.
- hard_conditions.monthly_rent: 월세 조건. 관리비 포함 여부도 여기에 둔다.
- soft_conditions.convenience_facilities: 편의 시설. 편의점, 마트, 병원, 약국, 카페, 세탁소 등.
- soft_conditions.pests: 벌레 여부. 벌레, 바퀴벌레, 해충 회피.
- soft_conditions.default_options: 기본 옵션. 에어컨, 냉장고, 세탁기, 침대 등.
- soft_conditions.basement: 반지하 여부.
- soft_conditions.mold: 곰팡이, 습기, 결로.

기존 state를 유지하면서 새 유저 메시지에 나온 조건만 병합한다.
모르는 값은 null 또는 빈 배열로 둔다.
하드 조건 위치/교통과 월세가 비어 있으면 missing_required_conditions에 넣는다.
next_question에는 다음에 물어볼 한 문장만 넣는다.
소프트 조건을 하나 이상 받았거나 사용자가 "없어", "더 없어"처럼 추가 조건이 없다고 말하면 is_complete=true, next_action="recommend_listings"로 둔다.
""".strip()


class RoomConditionAgent:
    def __init__(self, *, use_solar: bool = True, api_key: str | None = None) -> None:
        self.use_solar = use_solar
        self.api_key = api_key
        self.state = create_empty_conditions()

    def reset(self) -> ConditionState:
        self.state = create_empty_conditions()
        return deepcopy(self.state)
    
    def _deep_merge(self, base, new):
        if isinstance(base, dict) and isinstance(new, dict):
            merged = deepcopy(base)
            for key, value in new.items():
                if key in merged:
                    merged[key] = self._deep_merge(merged[key], value)
                else:
                    merged[key] = deepcopy(value)
            return merged

        if isinstance(base, list) and isinstance(new, list):
            result = list(base)
            for item in new:
                if item not in result:
                    result.append(item)
            return result

        if new is None:
            return deepcopy(base)
        return deepcopy(new)

    def handle_message(self, user_message: str) -> ConditionState:
        if self.use_solar and (self.api_key or get_solar_api_key()):
            try:
                self.state = self._handle_with_solar(user_message)
                return deepcopy(self.state)
            except SolarClientError:
                self.state = apply_rule_extraction(self.state, user_message)
                self.state["agent_mode"] = "rule_fallback"
                return deepcopy(self.state)

        self.state = apply_rule_extraction(self.state, user_message)
        self.state["agent_mode"] = "rule"
        return deepcopy(self.state)

    def _handle_with_solar(self, user_message: str) -> ConditionState:
        prompt = "\n\n".join(
            [
                SYSTEM_PROMPT,
                json.dumps(
                    {
                        "current_state": self.state,
                        "user_message": user_message,
                        "required_output_shape": create_empty_conditions(),
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "current_state": self.state,
                        "user_message": user_message,
                        "required_output_shape": create_empty_conditions(),
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        solar_state = call_upstage_json(prompt=prompt, messages=messages, api_key=self.api_key)
        next_state = self._deep_merge(self.state, solar_state)
        next_state = apply_rule_extraction(next_state, user_message)
        next_state["agent_mode"] = "solar"
        return update_missing_and_question(next_state)
