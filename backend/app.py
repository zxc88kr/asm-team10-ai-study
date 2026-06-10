from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import RoomConditionAgent, create_empty_conditions, ListingCurator


DEFAULT_SESSION_ID = "default"
DEFAULT_USE_SOLAR = os.getenv("ROOM_AGENT_USE_SOLAR", "true").lower() not in {"0", "false", "no"}
logger = logging.getLogger("uvicorn.error")


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
        "agent_logs": _condition_logs(state),
    }


def _condition_logs(state: dict[str, Any]) -> list[str]:
    """대화형 조건 수집 단계의 AI 진행 상황을 사람이 읽을 수 있는 로그로 만든다."""
    hard = state.get("hard_conditions", {})
    location = hard.get("location_transport", {})
    rent = hard.get("monthly_rent", {})
    soft = state.get("soft_conditions", {})
    logs = [
        f"조건 추출 엔진: {state.get('agent_mode', 'unknown')}",
        "하드 조건 확인: 위치/교통, 월세",
    ]

    if location.get("landmarks") or location.get("areas") or location.get("commute_time_max_minutes") is not None:
        logs.append("위치/교통 조건 업데이트 완료")
    if rent.get("max_manwon") is not None:
        logs.append("월세 조건 업데이트 완료")

    soft_count = 0
    facilities = soft.get("convenience_facilities", {})
    options = soft.get("default_options", {})
    if facilities.get("required") or facilities.get("preferred"):
        soft_count += 1
    if options.get("required") or options.get("preferred"):
        soft_count += 1
    for key in ("pests", "basement", "mold"):
        if soft.get(key, {}).get("avoid") is not None:
            soft_count += 1
    if soft_count > 0:
        logs.append(f"소프트 조건 {soft_count}개 반영")

    next_action = state.get("next_action")
    if next_action == "recommend_listings" or state.get("top_properties") is not None:
        logs.append("조건 수집 완료: 추천 단계 준비")
    elif state.get("missing_required_conditions"):
        logs.append(f"추가 질문 필요: {', '.join(state['missing_required_conditions'])}")
    else:
        logs.append("소프트 조건 확인 중")

    return logs


def _log_agent_logs(endpoint: str, session_id: str, logs: list[str]) -> None:
    clean_session_id = session_id.strip() or DEFAULT_SESSION_ID
    for log in logs:
        logger.info("[agent] endpoint=%s session_id=%s %s", endpoint, clean_session_id, log)


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
    response = _response(session_id, state)
    _log_agent_logs("/agent/message", session_id, response["agent_logs"])
    return response


@app.post("/agent/reset")
def agent_reset(payload: AgentResetRequest) -> dict[str, Any]:
    session_id = payload.session_id.strip() or DEFAULT_SESSION_ID
    _sessions[session_id] = RoomConditionAgent(use_solar=_use_solar(payload.use_solar))
    state = _sessions[session_id].reset()
    response = _response(session_id, state)
    _log_agent_logs("/agent/reset", session_id, response["agent_logs"])
    return response


class RecommendRequest(BaseModel):
    conditions: dict = Field(...)
    session_id: str = DEFAULT_SESSION_ID
    top_n: int = Field(default=5, ge=1, le=10)
    use_solar: bool | None = None


@app.post("/agent/recommend")
def agent_recommend(payload: RecommendRequest) -> dict[str, Any]:
    session_id = payload.session_id.strip() or DEFAULT_SESSION_ID
    curator = ListingCurator(use_solar=_use_solar(payload.use_solar))
    result = curator.recommend(
        conditions=payload.conditions,
        session_id=session_id,
        top_n=payload.top_n,
    )
    result["agent_logs"] = [
        f"추천 엔진: {'solar' if _use_solar(payload.use_solar) else 'rule'}",
        "조건 JSON 기반 후보 매물 점수 계산",
        f"상위 매물 {len(result.get('top_properties', []))}개 반환",
    ]
    _log_agent_logs("/agent/recommend", session_id, result["agent_logs"])
    return result
