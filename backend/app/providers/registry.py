"""Provider 선택기. 환경변수 ``ROOMPILOT_PROVIDER`` (mock | upstage), 기본 mock."""

from __future__ import annotations

import os

from app.providers.base import Provider

_override: Provider | None = None
_cached: Provider | None = None


def set_provider(provider: Provider | None) -> None:
    """테스트/런타임에서 강제 주입. None이면 환경변수 기반으로 복귀."""
    global _override, _cached
    _override = provider
    _cached = None


def get_provider() -> Provider:
    global _cached
    if _override is not None:
        return _override
    if _cached is not None:
        return _cached
    kind = os.getenv("ROOMPILOT_PROVIDER", "mock").lower()
    if kind == "upstage":
        from app.providers.upstage import UpstageProvider

        _cached = UpstageProvider()
    else:
        from app.providers.mock import MockProvider

        _cached = MockProvider()
    return _cached
