# RoomPilot Backend

`RoomPilot_데모시나리오.md`('민지의 첫 자취집 찾기')를 LangGraph 3-에이전트로 구현한 백엔드.
설계 출처: [`AI_에이전트_구현스펙.md`](AI_에이전트_구현스펙.md) · [`LangGraph_오케스트레이션_상세.md`](LangGraph_오케스트레이션_상세.md).

## 핵심 특징

- **단일 `StateGraph`** 에 3 에이전트(니즈 통역사 / 매물 큐레이터 / 입지 해설사)를 노드로 배치.
- **Provider 추상화** — LLM·임베딩·Groundedness를 인터페이스 뒤로 숨겨, `mock`(기본)이면
  **API 키 없이 오프라인으로 전체 그래프가 결정적으로 동작**한다. `upstage`면 실제 Solar API 호출.
- **환각 4중 방어** — 근거 인용 강제(스키마) → 구조 강제(JSON schema) → Groundedness 게이트 →
  미지 정보 회피("지어내지 않음").
- **HITL** — 역질문(`discover`)·우선순위 편집(`prioritize`)에서 `interrupt()`로 멈춰 사용자 입력을 받는다.
- **루프백** — "월세 +5만" 한마디로 `ingest`의 edit 분기 → `filter`부터 재추천.

## 빠른 실행 (오프라인, API 키 불필요)

```bash
cd backend
pip install "langgraph>=0.2"            # mock 경로는 langgraph만 있으면 됨
python -m pytest                        # 전체 테스트 (민지 시나리오 E2E 포함)
python demo.py                          # 콘솔에서 민지 시나리오 9턴 재생
```

## API 서버

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# POST /session                  → {session_id}
# POST /session/{id}/message     → SSE (card/metric/question/ranked/location/message)
# POST /session/{id}/resume      → SSE (interrupt 응답: 역질문/우선순위/매물선택)
```

## 실제 Upstage 연동

```bash
export ROOMPILOT_PROVIDER=upstage
export UPSTAGE_API_KEY=up_xxx
```

> ⚠️ 출고 전 검증(구현스펙 §13): Groundedness Check 엔드포인트·반환값, `solar-pro2` 가용성,
> `response_format=json_schema` 준수율. `app/providers/upstage.py`는 호출 형태 **초안**이며 라이브 검증 후 사용.

## 구조

```
app/
  graph.py            StateGraph 조립 + 체크포인터
  runtime.py          새 발화 vs interrupt 재개 판별, SSE/동기 드라이버
  state.py            AgentState · 카드 리듀서 · 차별 지표
  scoring.py          순수 점수 로직(카드↔매물 매칭, 가중 합산)
  blindspots.py       사각지대 체크리스트
  prompts.py          시스템 프롬프트 + 구조화 출력 스키마
  agents/             ingest·extract·discover·prioritize·filter·embed·score·ground·location·respond
  providers/          base(인터페이스) · mock(오프라인) · upstage(실 API) · registry
  data/               listings.json(부산대 시드) · seed.py
tests/                state·scoring·blindspots 단위 + 민지 시나리오 E2E
```

## 시드 데이터 / 점수에 대한 주의

- 매물은 **시드(가상) 데이터**(부산대·장전동)이며 실거래 매물이 아니다. 입지 수치는 데모용 가정값.
- mock 점수(A92·B62·C34·D96)는 **규칙 기반으로 계산된 값**이다. 데모 시나리오 문서의
  86·78·71·91은 예시 수치이며, mock은 **순위(A>B>C, 루프백 후 D>A>B)** 를 재현하는 것을 목표로 한다.
- 프론트엔드 `types.ts`의 `CardSource`는 `said|inferred` 2값이지만 백엔드는 `said|extracted|discovered`
  3값을 쓴다(발굴 🟧 구분 목적). FE 연동 시 `extracted|discovered → inferred`로 매핑하면 된다.
```
