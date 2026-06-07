from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import RoomConditionAgent, create_empty_conditions, ListingCurator


DEFAULT_SESSION_ID = "default"
DEFAULT_USE_SOLAR = os.getenv("ROOM_AGENT_USE_SOLAR", "true").lower() not in {"0", "false", "no"}


class AgentMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str = DEFAULT_SESSION_ID
    use_solar: bool | None = None


class AgentResetRequest(BaseModel):
    session_id: str = DEFAULT_SESSION_ID
    use_solar: bool | None = None


app = FastAPI(
    title="RoomPilot Condition Agent API",
    version="0.1.0",
    description="Chat-based room condition extraction agent.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: dict[str, RoomConditionAgent] = {}


def _use_solar(value: bool | None) -> bool:
    return DEFAULT_USE_SOLAR if value is None else value


def _get_agent(session_id: str, use_solar: bool | None = None) -> RoomConditionAgent:
    clean_session_id = session_id.strip() or DEFAULT_SESSION_ID
    if clean_session_id not in _sessions:
        _sessions[clean_session_id] = RoomConditionAgent(use_solar=_use_solar(use_solar))
    return _sessions[clean_session_id]


def _response(session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": session_id.strip() or DEFAULT_SESSION_ID,
        **state,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/agent/schema")
def agent_schema() -> dict[str, Any]:
    return create_empty_conditions()


@app.post("/agent/message")
def agent_message(payload: AgentMessageRequest) -> dict[str, Any]:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    session_id = payload.session_id.strip() or DEFAULT_SESSION_ID
    agent = _get_agent(session_id, payload.use_solar)
    state = agent.handle_message(message)
    return _response(session_id, state)


@app.post("/agent/reset")
def agent_reset(payload: AgentResetRequest) -> dict[str, Any]:
    session_id = payload.session_id.strip() or DEFAULT_SESSION_ID
    _sessions[session_id] = RoomConditionAgent(use_solar=_use_solar(payload.use_solar))
    state = _sessions[session_id].reset()
    return _response(session_id, state)


class RecommendRequest(BaseModel):
    conditions: dict = Field(...)
    session_id: str = DEFAULT_SESSION_ID
    top_n: int = Field(default=3, ge=1, le=10)
    use_solar: bool | None = None


@app.post("/agent/recommend")
def agent_recommend(payload: RecommendRequest) -> dict[str, Any]:
    session_id = payload.session_id.strip() or DEFAULT_SESSION_ID
    curator = ListingCurator(use_solar=_use_solar(payload.use_solar))
    return curator.recommend(
        conditions=payload.conditions,
        session_id=session_id,
        top_n=payload.top_n,
    )
