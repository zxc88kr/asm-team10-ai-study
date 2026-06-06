"""응답 합성 — intent/stage별 답변 텍스트(추천 요약 / 환각-회피 / 루프백 델타 / 입지 해설).

데모 결정성을 위해 템플릿 기반(LLM 미사용). 실연동 시 provider로 문장 다듬기 가능.
"""

from __future__ import annotations

from app.data.seed import get_listing
from app.events import emit
from app.state import AgentState, differentiation_ratio

_MEDALS = ["🥇", "🥈", "🥉"]


def respond_node(state: AgentState) -> dict:
    text = compose_reply(state)
    emit({"type": "message", "role": "ai", "text": text})
    new_stage = "listings" if state.get("ranked") else state.get("stage", "needs")
    return {"messages": [{"role": "assistant", "content": text}], "stage": new_stage}


def compose_reply(state: AgentState) -> str:
    intent = state.get("intent", "")
    cards = state.get("cards", [])
    ranked = state.get("ranked", [])
    if intent == "edit_condition":
        return _delta_reply(state)
    if intent == "ask_listing":
        return _ask_listing_reply(state)
    if intent in ("ask_location", "select_listing") and state.get("location_analysis"):
        return _location_reply(state)
    if state.get("stage") == "needs" and not any(c.kind == "soft" for c in cards):
        return (
            "좋아요, 카드로 잡아뒀어요. 이제 생활 얘기를 좀 들려주세요. "
            "평소 하루가 어떻게 흘러가요? 학교 가는 시간, 알바, 밥 같은 거요."
        )
    if ranked:
        return _topn_reply(state)
    return "조건을 조금만 더 들려주세요."


def _topn_reply(state: AgentState) -> str:
    cards = state.get("cards", [])
    ratio = differentiation_ratio(cards)
    lines = []
    for i, sl in enumerate(state["ranked"][:3]):
        listing = get_listing(sl.listing_id)
        lines.append(f"{_MEDALS[i]} {listing.name} {sl.score}점")
    head = (
        f"민지님이 직접 말한 건 {ratio['said']}가지였지만, "
        f"RoomPilot은 {ratio['derived']}가지 숨은 조건을 같이 찾았어요({ratio['ratio']}). "
    )
    return head + "추천 TOP3 — " + ", ".join(lines) + "."


def _delta_reply(state: AgentState) -> str:
    prev, cur = state.get("prev_candidate_count", 0), state.get("candidate_count", 0)
    ranked = state.get("ranked", [])
    if not ranked:
        return f"후보가 {prev}건 → {cur}건으로 바뀌었지만 조건에 맞는 매물이 없어요."
    top = get_listing(ranked[0].listing_id)
    msg = f"후보가 {prev}건 → {cur}건으로 늘었어요. 새로 들어온 매물로 다시 줄세웠어요. "
    if ranked[0].listing_id != state.get("prev_top_id"):
        msg += f"이제 {top.name}({ranked[0].score}점)가 새로 1등이에요 — 월 {top.rent}만 원."
    else:
        msg += f"여전히 {top.name}({ranked[0].score}점)가 1순위예요."
    return msg


def _ask_listing_reply(state: AgentState) -> str:
    text = state["messages"][-1].content
    listing = _detect_listing(text, state)
    if listing is None:
        return "어느 매물을 말씀하시는 걸까요? A·B·C 중에서 알려주세요."
    for attr in ("방음", "층간소음", "엘리베이터", "주차"):
        if attr in text and attr not in listing.desc:
            return (
                f"{listing.name} 설명에는 {attr} 관련 정보가 없어서 제가 지어내진 않을게요. "
                "입주 전 직접 확인이 필요한 항목으로 체크해 둘게요."
            )
    return f"{listing.name}({listing.area}) 설명 기준으로 답변드릴게요: {listing.desc}"


def _location_reply(state: AgentState) -> str:
    analysis = state["location_analysis"]
    lid = next(iter(analysis))
    listing = get_listing(lid)
    loc = analysis[lid]
    note = loc.get("commute", {}).get("mainNote", "")
    return (
        f"{listing.name} 입지를 민지님 카드(밤 11시 귀가·통학) 기준으로 풀어볼게요. {note}. "
        f"통학 약 {loc.get('commute', {}).get('totalMinutes', '?')}분."
    )


def _detect_listing(text: str, state: AgentState):
    for lid in ("A", "B", "C", "D"):
        if lid in text:
            try:
                return get_listing(lid)
            except KeyError:
                continue
    for sl in state.get("ranked", []):
        listing = get_listing(sl.listing_id)
        if listing.name in text:
            return listing
    return None
