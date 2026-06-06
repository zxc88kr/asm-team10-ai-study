"""발화에서 금액(만원)·텍스트를 안전하게 파싱하는 유틸. mock/upstage 공용."""

from __future__ import annotations

import re

_RANGE = re.compile(r"(\d+)\s*[~\-∼]\s*(\d+)")
_NUM = re.compile(r"\d+")


def won_after(text: str, keywords: list[str]) -> int | None:
    """키워드 바로 뒤 금액(만원). '5~7만' 같은 범위면 최댓값. 키워드 직후 좁은 창만 본다."""
    for kw in keywords:
        idx = text.find(kw)
        if idx == -1:
            continue
        window = text[idx : idx + 15]
        rng = _RANGE.search(window)
        if rng:
            return max(int(rng.group(1)), int(rng.group(2)))
        num = _NUM.search(window)
        if num:
            return int(num.group())
    return None


def message_text(content: object) -> str:
    """LLM 메시지 content(str | list[str|dict])를 평문으로 정규화."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
        return " ".join(p for p in parts if p).strip()
    return str(content)
