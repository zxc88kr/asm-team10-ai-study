"""테스트 공통 설정 — mock provider 강제."""

import os

import pytest

os.environ.setdefault("ROOMPILOT_PROVIDER", "mock")


@pytest.fixture(autouse=True)
def _use_mock_provider():
    from app.providers import set_provider
    from app.providers.mock import MockProvider

    set_provider(MockProvider())
    yield
    set_provider(None)
