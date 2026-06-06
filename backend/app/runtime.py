"""실행·재개 글루 (오케스트레이션 §7).

이번 호출이 새 발화인지 interrupt 재개인지 ``get_state().next``로 판별한다.
- ``drive``: 동기 드라이버(테스트·CLI용) — 이벤트 목록과 최종 상태를 반환.
- ``run_turn``: 비동기 스트림(SSE 서버용).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

from langgraph.types import Command

from app.graph import GRAPH
from app.state import init_state


def new_session() -> str:
    return uuid.uuid4().hex


def _config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _is_fresh(config: dict) -> bool:
    return not GRAPH.get_state(config).values


def has_pending_interrupt(session_id: str) -> bool:
    return bool(GRAPH.get_state(_config(session_id)).next)


def _build_input(config: dict, user_text: str | None, resume: Any) -> Command | dict[str, Any]:
    if resume is not None and bool(GRAPH.get_state(config).next):
        return Command(resume=resume)
    inp: dict[str, Any] = dict(init_state()) if _is_fresh(config) else {}
    inp["messages"] = [{"role": "user", "content": user_text or ""}]
    return inp


def _interrupt_event(payload: Any) -> dict:
    item = payload[0] if isinstance(payload, (list, tuple)) else payload
    raw = getattr(item, "value", item)
    value = dict(raw) if isinstance(raw, dict) else {}
    # value 자체에 "type"(discover_question/edit_priority/...)이 있으므로 questionType으로 보존.
    subtype = value.pop("type", None)
    return {"type": "question", "questionType": subtype, **value}


def _iter_events(mode: str, chunk: Any) -> Iterator[dict]:
    if mode == "custom":
        yield chunk
    elif mode == "updates":
        for node, payload in chunk.items():
            if node == "__interrupt__":
                yield _interrupt_event(payload)


def drive(session_id: str, user_text: str | None = None, resume: Any = None) -> dict:
    config = _config(session_id)
    graph_input = _build_input(config, user_text, resume)
    events: list[dict] = []
    for mode, chunk in GRAPH.stream(graph_input, config, stream_mode=["custom", "updates"]):
        events.extend(_iter_events(mode, chunk))
    snap = GRAPH.get_state(config)
    return {"events": events, "state": snap.values, "pending": bool(snap.next), "next": snap.next}


async def run_turn(
    session_id: str, user_text: str | None = None, resume: Any = None
) -> AsyncIterator[dict]:
    config = _config(session_id)
    graph_input = _build_input(config, user_text, resume)
    async for mode, chunk in GRAPH.astream(
        graph_input, config, stream_mode=["custom", "updates"]
    ):
        for event in _iter_events(mode, chunk):
            yield event
    yield {"type": "done"}
