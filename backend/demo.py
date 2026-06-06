"""콘솔에서 '민지의 첫 자취집 찾기' 시나리오를 재생한다.

    python demo.py                              # mock(오프라인, 결정적)
    ROOMPILOT_PROVIDER=upstage python demo.py   # 실 Solar API(비결정적)

interrupt-적응형 드라이버: 각 발화 후 HITL 질문이 뜨면 질문 종류(questionType)를 보고
적절한 응답을 자동 생성한다. 실제 LLM이 역질문 횟수/종류를 다르게 내도 흐름이 끊기지 않는다.
"""

from __future__ import annotations

from app.config import load_dotenv
from app.runtime import drive, new_session

load_dotenv()  # ROOMPILOT_PROVIDER=upstage 일 때 .env 의 UPSTAGE_API_KEY 사용

# 사용자가 '말하는' 5개 발화(니즈 2 + 질문/입지/루프백 3). 역질문 응답은 아래에서 자동 생성.
UTTERANCES = [
    ("① 니즈", "부산대 신입인데 자취 처음이에요. 보증금 1000에 월세 50 정도로 보고 있어요. 관리비는 5~7만까지 괜찮아요."),
    ("① 생활", "밤 11시쯤 집에 들어가요. 본가가 서울이라 자주 못 와요. 요리도 자주 하는 편이에요."),
    ("③ 질문(방음)", "C는 방음 어때요?"),
    ("④ 입지", "입지 설명해줘"),
    ("⑤ 루프백", "월세 5만 더 올리면 뭐가 달라져요?"),
]

_DISCOVER_ANSWERS = {
    "safety": "어두운 골목은 무서울 것 같아요. 가로등 있는 길이 좋아요.",
    "security": "택배 보관함이나 공동현관 보안도 챙겨주세요.",
    "light": "채광 좋고 곰팡이·습기 없는 집이 좋아요.",
    "noise": "방음도 신경 써주세요.",
    "kitchen": "주방이 분리된 게 좋아요.",
}


def auto_resume(question: dict):
    """HITL 질문 종류별 자동 응답 생성."""
    qtype = question.get("questionType")
    if qtype == "edit_priority":
        cats = question.get("categories", [])
        order = [c for c in ("safety", "budget", "commute") if c in cats] or cats
        return {"order": order}
    if qtype == "select_listing":
        options = question.get("options", [])
        return {"listing_id": options[0] if options else "A"}
    # discover_question (또는 기타) → 발화형 답변
    return _DISCOVER_ANSWERS.get(question.get("category"), "네, 그것도 중요해요.")


def _print(result: dict) -> None:
    for e in result["events"]:
        t = e.get("type")
        if t == "card":
            c = e["card"]
            tag = {"said": "🟦", "extracted": "🟩", "discovered": "🟧"}.get(c["source"], "▫")
            print(f"   {tag} [{c['source']}] {c['label']:14s} ← {c['reason'][:26]}")
        elif t == "metric":
            print(f"   📊 차별 지표 {e['ratio']}  (직접 {e['said']} : 발굴/추출 {e['derived']})")
        elif t == "question":
            kind = e.get("category") or e.get("questionType")
            print(f"   ⏸ 질문[{kind}]: {(e.get('text') or '')[:54]}")
        elif t == "ranked":
            print(f"   🏅 추천: {[(x['listingId'], x['score']) for x in e['ranked']]}")
        elif t == "location":
            print(f"   🗺  입지 분석: {e['listingId']}")
        elif t == "message":
            print(f"   🤖 {e['text']}")


def _last_question(result: dict) -> dict | None:
    qs = [e for e in result["events"] if e.get("type") == "question"]
    return qs[-1] if qs else None


def run_utterance(sid: str, label: str, text: str) -> None:
    print(f"\n=== {label} ===")
    print(f"   👤 {text}")
    result = drive(sid, text)
    _print(result)
    guard = 0
    while result.get("pending") and guard < 8:  # interrupt 적응 루프(무한루프 방지)
        guard += 1
        question = _last_question(result)
        if question is None:
            break
        payload = auto_resume(question)
        print(f"   ▶ resume: {payload}")
        result = drive(sid, resume=payload)
        _print(result)


def main() -> None:
    sid = new_session()
    for label, text in UTTERANCES:
        run_utterance(sid, label, text)


if __name__ == "__main__":
    main()
