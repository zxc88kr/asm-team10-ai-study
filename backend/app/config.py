"""환경설정 — backend/.env 를 의존성 없이 로드한다(python-dotenv 불필요)."""

from __future__ import annotations

import os
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_dotenv() -> None:
    """backend/.env 의 KEY=VALUE 를 os.environ 에 주입(기존 값은 보존)."""
    if not _ENV_PATH.exists():
        return
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())
