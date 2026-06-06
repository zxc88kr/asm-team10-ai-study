"""RoomPilot backend — LangGraph 3-agent orchestration.

데모 시나리오('민지의 첫 자취집 찾기')를 구현한 백엔드.
LLM/임베딩/Groundedness는 ``app.providers`` 인터페이스 뒤로 추상화되어,
``ROOMPILOT_PROVIDER=mock``(기본)이면 API 키 없이 오프라인으로 전체 그래프가 동작한다.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
