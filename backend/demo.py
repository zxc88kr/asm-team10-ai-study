"""콘솔에서 '민지의 첫 자취집 찾기' 9턴을 재생한다 (오프라인, mock provider).

    python demo.py
"""

from __future__ import annotations

from app.runtime import drive, new_session

# (라벨, 사용자 발화 또는 resume payload, resume 여부)
SCRIPT = [
    ("① 니즈", "부산대 신입인데 자취 처음이에요. 보증금 1000에 월세 50 정도로 보고 있어요. 관리비는 5~7만까지 괜찮아요.", False),
    ("① 생활", "밤 11시쯤 집에 들어가요. 본가가 서울이라 자주 못 와요. 요리도 자주 하는 편이에요.", False),
    ("↩ 역질문답(안전)", "어두운 골목은 무서울 것 같아요.", True),
    ("↩ 역질문답(택배)", "택배도 챙겨주세요.", True),
    ("↩ 역질문답(채광)", "곰팡이나 습기는 싫어요.", True),
    ("↩ 우선순위", {"order": ["safety", "budget", "commute"]}, True),
    ("③ 질문(방음)", "C는 방음 어때요?", False),
    ("④ 입지", "입지 설명해줘", False),
    ("⑤ 루프백", "월세 5만 더 올리면 뭐가 달라져요?", False),
]


def _print(result: dict) -> None:
    for e in result["events"]:
        t = e.get("type")
        if t == "card":
            c = e["card"]
            tag = {"said": "🟦", "extracted": "🟩", "discovered": "🟧"}.get(c["source"], "▫")
            print(f"   {tag} [{c['source']}] {c['label']:10s} ← {c['reason'][:30]}")
        elif t == "metric":
            print(f"   📊 차별 지표 {e['ratio']}  (직접 {e['said']} : 발굴/추출 {e['derived']})")
        elif t == "question":
            kind = e.get("category") or e.get("questionType")
            print(f"   ⏸ 질문[{kind}]: {(e.get('text') or '')[:60]}")
        elif t == "ranked":
            ids = [(x["listingId"], x["score"]) for x in e["ranked"]]
            print(f"   🏅 추천: {ids}")
        elif t == "location":
            print(f"   🗺  입지 분석: {e['listingId']}")
        elif t == "message":
            print(f"   🤖 {e['text']}")


def main() -> None:
    sid = new_session()
    for label, payload, is_resume in SCRIPT:
        print(f"\n=== {label} ===")
        if not is_resume:
            print(f"   👤 {payload}")
        else:
            print(f"   ▶ resume: {payload}")
        result = drive(sid, resume=payload) if is_resume else drive(sid, payload)
        _print(result)


if __name__ == "__main__":
    main()
