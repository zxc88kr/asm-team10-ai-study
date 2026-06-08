from __future__ import annotations

from copy import deepcopy

from .graph import AgentState, agent_graph
from .schema import ConditionState, create_empty_conditions


class RoomConditionAgent:
    def __init__(self, *, use_solar: bool = True, api_key: str | None = None) -> None:
        self.use_solar = use_solar
        self.api_key = api_key
        self._agent_state: AgentState = self._initial_state()

    def _initial_state(self) -> AgentState:
        return {
            "messages": [],
            "conditions": create_empty_conditions(),
            "use_solar": self.use_solar,
            "api_key": self.api_key,
        }

    def reset(self) -> ConditionState:
        self._agent_state = self._initial_state()
        return deepcopy(self._agent_state["conditions"])

    @property
    def state(self) -> ConditionState:
        return self._agent_state["conditions"]

    def handle_message(self, user_message: str) -> ConditionState:
        # 사용자 메시지를 히스토리에 추가한 뒤 그래프 실행
        self._agent_state = {
            **self._agent_state,
            "messages": [*self._agent_state["messages"], {"role": "user", "content": user_message}],
        }
        result = agent_graph.invoke(self._agent_state)
        self._agent_state = result
        return deepcopy(self._agent_state["conditions"])
