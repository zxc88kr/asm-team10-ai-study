"""LLM / 임베딩 / Groundedness 추상화 레이어.

그래프 노드는 ``get_provider()``만 의존하고, 실제 모델 호출은 Provider 구현에 위임한다.
``ROOMPILOT_PROVIDER=mock``(기본)이면 API 키 없이 결정적으로 동작(오프라인 E2E 가능),
``upstage``면 실제 Solar API를 호출한다.
"""

from app.providers.base import Provider
from app.providers.registry import get_provider, set_provider

__all__ = ["Provider", "get_provider", "set_provider"]
