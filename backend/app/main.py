"""FastAPI 앱 + SSE 라우트 (구현스펙 §10 / 오케스트레이션 §7, §8).

실행: uvicorn app.main:app --reload   (fastapi, sse-starlette, uvicorn 필요)
카드/추천/해설이 실시간으로 채워지는 UX이므로 SSE 스트리밍.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.runtime import new_session, run_turn

app = FastAPI(title="RoomPilot Backend", version="0.1.0")


class MsgIn(BaseModel):
    text: str


class ResumeIn(BaseModel):
    payload: Any


async def _sse(session_id: str, text: str | None = None, resume: Any = None):
    async for event in run_turn(session_id, text, resume):
        yield {"event": event.get("type", "message"), "data": json.dumps(event, ensure_ascii=False)}


@app.post("/session")
def create_session() -> dict:
    return {"session_id": new_session()}


@app.post("/session/{sid}/message")
async def message(sid: str, body: MsgIn) -> EventSourceResponse:
    return EventSourceResponse(_sse(sid, text=body.text))


@app.post("/session/{sid}/resume")
async def resume(sid: str, body: ResumeIn) -> EventSourceResponse:
    return EventSourceResponse(_sse(sid, resume=body.payload))


@app.get("/health")
def health() -> dict:
    from app.providers import get_provider

    return {"ok": True, "provider": get_provider().name}
