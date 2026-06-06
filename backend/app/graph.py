"""그래프 조립 (오케스트레이션 §6).

ingest → (needs: extract → discover↺ / prioritize) → filter → embed_rank → score
       → ground_check → respond → END
루프백은 ingest의 edit 분기로 filter부터 재실행.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph

from app.agents.curator import (
    embed_rank_node,
    filter_node,
    ground_check_node,
    score_node,
)
from app.agents.location import location_node
from app.agents.needs import (
    discover_node,
    extract_node,
    prioritize_node,
    route_after_extract,
)
from app.agents.respond import respond_node
from app.agents.router import ingest_node, route_from_ingest
from app.state import AgentState, ConditionCard, MatchResult, ScoredListing

# 체크포인트 직렬화 시 상태에 담기는 pydantic 모델을 명시 허용(미등록 경고/차단 방지).
_SERDE = JsonPlusSerializer(
    allowed_msgpack_modules=(ConditionCard, MatchResult, ScoredListing)
)


def _default_checkpointer() -> MemorySaver:
    return MemorySaver(serde=_SERDE)

_NODES = {
    "ingest": ingest_node,
    "extract": extract_node,
    "discover": discover_node,
    "prioritize": prioritize_node,
    "filter": filter_node,
    "embed_rank": embed_rank_node,
    "score": score_node,
    "ground_check": ground_check_node,
    "location": location_node,
    "respond": respond_node,
}


def build_graph(checkpointer=None):
    g = StateGraph(AgentState)
    for name, fn in _NODES.items():
        g.add_node(name, fn)

    g.add_edge(START, "ingest")
    g.add_conditional_edges(
        "ingest",
        route_from_ingest,
        {"extract": "extract", "filter": "filter", "location": "location", "respond": "respond"},
    )
    g.add_conditional_edges(
        "extract",
        route_after_extract,
        {"discover": "discover", "prioritize": "prioritize", "respond": "respond"},
    )
    g.add_edge("discover", "extract")  # 역질문 답 → 재추출 (루프)
    g.add_edge("prioritize", "filter")

    g.add_edge("filter", "embed_rank")
    g.add_edge("embed_rank", "score")
    g.add_edge("score", "ground_check")
    g.add_edge("ground_check", "respond")

    g.add_edge("location", "respond")
    g.add_edge("respond", END)
    return g.compile(checkpointer=checkpointer or _default_checkpointer())


GRAPH = build_graph()
