"""실제 Upstage Solar API 스모크 테스트.

구현스펙 §13의 '출고 전 검증' 항목을 개별적으로 점검한다. 한 항목이 실패해도
나머지는 계속 진행하고, 마지막에 PASS/FAIL 요약을 출력한다.

실행:
    cd backend
    # 방법 1) .env 파일에 UPSTAGE_API_KEY=up_xxx 작성 후:
    python scripts/smoke_upstage.py
    # 방법 2) 환경변수로:
    UPSTAGE_API_KEY=up_xxx python scripts/smoke_upstage.py

점검 항목:
    A. ChatUpstage 기본 호출 (solar-pro2 등 후보 모델 가용성)
    B. 구조화 출력(response_format=json_schema) 준수
    C. 임베딩(solar-embedding-1-large) 차원
    D. Groundedness Check 엔드포인트·반환값
    E. UpstageProvider로 그래프 1턴 E2E
"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

PRO_CANDIDATES = ["solar-pro2", "solar-pro", "solar-pro3"]
from app.config import load_dotenv  # noqa: E402

_results: list[tuple[str, bool, str]] = []


def _record(name: str, ok: bool, detail: str = "") -> None:
    mark = "✅ PASS" if ok else "❌ FAIL"
    print(f"  {mark}  {name}" + (f"  — {detail}" if detail else ""))
    _results.append((name, ok, detail))


def probe_chat() -> str | None:
    from langchain_upstage import ChatUpstage

    for model in PRO_CANDIDATES:
        try:
            resp = ChatUpstage(model=model, temperature=0).invoke("한 단어로 인사해줘")
            _record(f"A. ChatUpstage [{model}]", True, repr(resp.content)[:40])
            return model
        except Exception as exc:  # noqa: BLE001
            _record(f"A. ChatUpstage [{model}]", False, f"{type(exc).__name__}: {exc}"[:80])
    return None


def probe_structured(model: str) -> None:
    from langchain_upstage import ChatUpstage

    from app.prompts import INTENT_SCHEMA, INTENT_SYSTEM

    try:
        out = ChatUpstage(model=model, temperature=0).with_structured_output(INTENT_SCHEMA).invoke(
            [
                {"role": "system", "content": INTENT_SYSTEM},
                {"role": "user", "content": "월세 5만 더 올리면?"},
            ]
        )
        ok = isinstance(out, dict) and "intent" in out
        _record("B. 구조화 출력(json_schema)", ok, repr(out)[:80])
    except Exception as exc:  # noqa: BLE001
        _record("B. 구조화 출력(json_schema)", False, f"{type(exc).__name__}: {exc}"[:80])


def probe_embedding() -> None:
    from langchain_upstage import UpstageEmbeddings

    try:
        vec = UpstageEmbeddings(model="solar-embedding-1-large").embed_query("야간 안전 동선")
        _record("C. 임베딩 차원", bool(vec), f"dim={len(vec)}")
    except Exception as exc:  # noqa: BLE001
        _record("C. 임베딩 차원", False, f"{type(exc).__name__}: {exc}"[:80])


def probe_groundedness() -> None:
    # groundedness-check 전용 모델 폐기 → LLM-as-Judge(solar-mini)로 검증.
    from app.providers.upstage import UpstageProvider

    try:
        provider = UpstageProvider()
        ctx = "부산대역 도보 5분, 남향이라 채광 좋고 환기 잘 됨."
        good = provider.check_grounded(ctx, "남향이라 채광 좋고 환기 잘 됨")
        bad = provider.check_grounded(ctx, "지하 단칸방이라 방음이 완벽하다")
        ok = good == "grounded" and bad in ("notGrounded", "notSure")
        _record("D. Groundedness (LLM judge)", ok, f"근거O→{good!r} / 근거X→{bad!r}")
    except Exception as exc:  # noqa: BLE001
        _record("D. Groundedness (LLM judge)", False, f"{type(exc).__name__}: {exc}"[:80])


def probe_end_to_end() -> None:
    try:
        os.environ["ROOMPILOT_PROVIDER"] = "upstage"
        from app.providers import set_provider
        from app.providers.upstage import UpstageProvider
        from app.runtime import drive, new_session

        set_provider(UpstageProvider())
        sid = new_session()
        r = drive(sid, "부산대 신입인데 보증금 1000에 월세 50 정도로 보고 있어요.")
        cards = [e for e in r["events"] if e.get("type") == "card"]
        labels = [c["card"]["label"] for c in cards]
        _record("E. 그래프 1턴 E2E", bool(cards), f"cards={labels}")
    except Exception as exc:  # noqa: BLE001
        _record("E. 그래프 1턴 E2E", False, f"{type(exc).__name__}: {exc}"[:80])
        traceback.print_exc()


def main() -> int:
    load_dotenv()
    if not os.environ.get("UPSTAGE_API_KEY"):
        print("❌ UPSTAGE_API_KEY 가 없습니다. backend/.env 에 작성하거나 환경변수로 주입하세요.")
        return 2

    print("=== Upstage Solar 스모크 테스트 ===")
    model = probe_chat()
    if model:
        probe_structured(model)
    probe_embedding()
    probe_groundedness()
    if model:
        probe_end_to_end()

    passed = sum(1 for _, ok, _ in _results if ok)
    print(f"\n=== 요약: {passed}/{len(_results)} PASS ===")
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
