"""대화형 CLI — 터미널에서 RoomPilot 백엔드를 직접 테스트한다.

    python chat.py                              # mock(오프라인)
    ROOMPILOT_PROVIDER=upstage python chat.py   # 실 Solar API

명령:
    /new   새 세션 시작
    /quit  종료
HITL 질문(역질문/우선순위/매물선택)이 뜨면 그 자리에서 답을 입력하면 된다.
    - 역질문        : 자유 문장 (예: "어두운 골목은 무서워요")
    - 우선순위 편집 : 쉼표로 순서 (예: "safety,budget,commute")  / 빈 입력이면 제시된 순서
    - 매물 선택     : 매물 id (예: "A")
"""

from __future__ import annotations

from app.config import load_dotenv
from app.providers import get_provider
from app.runtime import drive, new_session
from demo import _print  # 이벤트 출력 재사용

load_dotenv()


def _pending_question(result: dict) -> dict | None:
    if not result.get("pending"):
        return None
    qs = [e for e in result["events"] if e.get("type") == "question"]
    return qs[-1] if qs else None


def _parse_answer(question: dict, raw: str) -> dict | str:
    qtype = question.get("questionType")
    if qtype == "edit_priority":
        order = [c.strip() for c in raw.split(",") if c.strip()]
        return {"order": order or question.get("categories", [])}
    if qtype == "select_listing":
        return {"listing_id": raw.strip() or (question.get("options") or ["A"])[0]}
    return raw  # discover_question → 자유 문장


def main() -> None:
    print(f"RoomPilot CLI  (provider={get_provider().name})  —  /new, /quit")
    sid = new_session()
    while True:
        try:
            text = input("\n👤 ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text in ("/quit", "/exit"):
            break
        if text == "/new":
            sid = new_session()
            print("   (새 세션 시작)")
            continue
        if not text:
            continue

        result = drive(sid, text)
        _print(result)
        while (question := _pending_question(result)) is not None:
            answer = input("   ↩ ").strip()
            payload = _parse_answer(question, answer)
            result = drive(sid, resume=payload)
            _print(result)


if __name__ == "__main__":
    main()
