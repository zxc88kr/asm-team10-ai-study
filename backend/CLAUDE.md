# RoomPilot Backend — Claude Code 가이드

Python · FastAPI · LangGraph 백엔드. 데모 시나리오(`RoomPilot_데모시나리오.md`, 민지)를
[`AI_에이전트_구현스펙.md`](AI_에이전트_구현스펙.md) · [`LangGraph_오케스트레이션_상세.md`](LangGraph_오케스트레이션_상세.md)
로 구현. 상세는 [`README.md`](README.md) 참고.

## 개발 명령어

```bash
# backend/ 디렉토리에서 실행
python -m pytest                 # 테스트 (민지 시나리오 E2E 포함)
python -m ruff check .           # 린트
python -m ruff check --fix .     # 린트 자동수정
python -m mypy                   # 타입체크
python -m compileall -q app tests demo.py chat.py scripts   # 빌드(컴파일) 확인

python demo.py                   # 콘솔 9턴 재생(mock)
python chat.py                   # 대화형 CLI
uvicorn app.main:app --reload    # SSE API 서버 (http://localhost:8000/docs)
ROOMPILOT_PROVIDER=upstage python scripts/smoke_upstage.py   # 실 API 점검
```

## 커밋 게이트 (4개 — 하나라도 실패 시 커밋 불가)

프론트엔드 규칙(lint/typecheck/test/build)을 백엔드 도구로 매핑한다.

```bash
python -m ruff check .       # lint      — 에러 0개
python -m mypy               # typecheck — Success
python -m pytest             # test      — 전체 통과
python -m compileall -q app tests demo.py chat.py scripts   # build — OK
```

커밋은 논리적 단위로 자동 분리한다. main 직접 push 금지 — feature 브랜치 → PR.

## 구조 / 규칙

- `app/` 코어, `app/agents/` 노드, `app/providers/` LLM 추상화(mock/upstage), `app/data/` 시드.
- **Provider 인터페이스**(`app/providers/base.py`)만 노드가 의존. mock은 오프라인 결정적, upstage는 실 API.
- 순수 로직(`scoring.py`·`state.py`·`blindspots.py`)은 LLM/IO 의존 없이 단위 테스트.
- LLM 노드 테스트는 mock provider로 결정적 검증(`tests/`).
- 새 비즈니스 로직엔 테스트 필수. `Any` 남용·미사용 import 금지(ruff/mypy가 잡음).
- `interrupt()` 앞에 부수효과 두지 말 것(재개 시 재실행). HITL 흐름은 오케스트레이션 §10 함정 참고.

## 금지사항

- `.env` 커밋 금지(gitignore됨). 시드 매물은 가상 데이터 — 실거래 아님 명시.
- `main` 직접 push 금지.
