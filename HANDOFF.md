# HANDOFF — RoomPilot (소마 10조)

> 갱신: 2026-06-06 · 다음 세션은 이 파일만 읽으면 바로 이어갈 수 있음.

## 한 줄 요약

첫 독립 청년의 *말로 표현 못 한 생활 니즈*를 LLM이 집 조건으로 **번역·발굴**해 근거와 함께
매물을 추천하는 3-에이전트. 부산대·장전동 시드. **LangGraph 백엔드 + 라이브 SSE 프론트엔드 +
Upstage Solar 실 LLM** 연동 완료. 이번 세션에서 **웹 전면 리디자인(랜딩+워크스페이스) · 지도(Leaflet)
· 매물 상세/액션 · 입지추천을 OSM 공공데이터(Nominatim/Overpass/OSRM) 실측으로 전환**까지 완료.

## 현재 상태

- 브랜치: `feat/backend-langgraph-skeleton` (전부 미커밋 — 논리 단위 커밋 + PR 대기)
- **백엔드 4게이트 통과**: ruff / mypy(38파일) / pytest(29) / compileall
- **프론트 4게이트 통과**: eslint(에러 0, Toast.tsx 경고 1은 기존 잔존) / tsc / vitest(43) / build
- 로컬 실행 중(데모 가능): FE `:5173`, BE `:8000`(provider=upstage)
- 직전 작업: **입지추천 실 공공데이터 전환** — 시드의 "가정값" 입지 수치를 OSM 실측으로 교체.
  데모 시나리오(Scene 5) 루프백 칩, 출처 배지, 주변 인프라 실측 카운트 UI 추가.

### 이번 세션에 한 것 (요약)
1. **UI 전면 리디자인**: 대화 시작 전 **랜딩 히어로**(LiveLanding) ↔ 시작 후 **워크스페이스**(채팅+인사이트) 분기.
   디자인 시스템(index.css) 정돈.
2. **지도**: Leaflet + OpenStreetMap(키 불필요). 캠퍼스+매물 마커, 순위 핀, 선택 강조(LiveMap).
3. **매물 상세 모달**(LiveListingModal): 가격/옵션/통학 동선/야간 안전/편의/장단점/AI코멘트 + 포커스 지도.
   액션: **찜(localStorage 영속)·AI 입지 분석(실 백엔드)·공유(navigator.share/클립보드)·길찾기(OSM)**.
4. **헤더 제목 클릭 → 홈(랜딩) 복귀**(reset). 스테퍼/랜딩 기능카드도 클릭 동작(섹션 스크롤/예시 채우기).
5. **입지 실데이터화**: `app/services/osm.py` + `scripts/enrich_listings.py` → `app/data/geo_cache.json`.
   seed 로더가 캐시 병합 → 통학 도보(OSRM)·주변 편의/안전(Overpass)이 실측값.
6. **WSL HMR 자동반영**: vite `server.watch.usePolling`(=/mnt 드라이브 inotify 미지원 우회).

## 아키텍처

```
provider 추상화: Provider(ABC) ─ MockProvider(오프라인 결정적) / UpstageProvider(실 Solar)
                 선택: ROOMPILOT_PROVIDER=mock|upstage  (키 없으면 mock 우회)

LangGraph StateGraph (app/agents/)
  router(ingest/route) → needs(extract/discover/prioritize, HITL interrupt())
                       → curator(filter/embed_rank/score/ground_check)
                       → location → respond
  state.py: AgentState(TypedDict), merge_cards 리듀서, differentiation_ratio,
            MemorySaver(JsonPlusSerializer allowlist)

입지 공공데이터 enrich (신규):
  scripts/enrich_listings.py → app/services/osm.py
    Nominatim(지오코딩) · Overpass(주변 POI 실측) · OSRM(도보 통학 실측)
    → app/data/geo_cache.json (좌표 주변 실측, ODbL)
  app/data/seed.py: 로드 시 geo_cache 병합 → geo(통학/역 도보분)·location(해설) 실데이터로 대체
    ※ 캐시는 시드 점수화에도 영향 → 시나리오 테스트는 실데이터 결과 기준으로 갱신됨

프론트(라이브):
  App: started(=user 발화 유무)로 LiveLanding ↔ 워크스페이스 분기, detailId로 모달 제어
  store/useLiveStore: SSE 이벤트 리듀서 + favorites(localStorage) + analyzeListing(=select_listing 발화)
```

## 핵심 파일

| 영역 | 파일 |
|---|---|
| 프롬프트/스키마 | `backend/app/prompts.py` — 모든 스키마 top-level `title` 필수 |
| 실 LLM | `backend/app/providers/upstage.py` · Mock `mock.py` (둘 다 analyze_location은 location.dataSource 보존) |
| 상태/리듀서 | `backend/app/state.py` · 점수/매칭 `scoring.py` |
| 에이전트 | `backend/app/agents/{router,needs,curator,location,respond}.py` |
| **입지 공공데이터** | `backend/app/services/osm.py` (Nominatim/Overpass/OSRM, 순수 파서+네트워크 분리) |
| **enrich 스크립트/캐시** | `backend/scripts/enrich_listings.py` → `backend/app/data/geo_cache.json` |
| 시드 로더 | `backend/app/data/seed.py` (geo_cache 병합) · 시드 `data/listings.json`(geo.lat/lng 포함) |
| API | `backend/app/main.py` — CORS, /session, /message(SSE), /resume(SSE), /listings, /health |
| FE 진입/분기 | `frontend/src/App.tsx` · `main.tsx`(leaflet css import) |
| FE API/타입 | `frontend/src/api/{client,types}.ts` (SSE=fetch+ReadableStream) |
| FE 스토어 | `frontend/src/store/useLiveStore.ts` (favorites·analyzeListing 추가) |
| FE 컴포넌트 | `frontend/src/components/live/{LiveTopBar,LiveLanding,LiveChat,LiveMetric,LiveConditions,LiveRecommendations,LiveMap,LiveListingModal}.tsx` |
| 디자인 시스템 | `frontend/src/index.css` |

## 실행

```bash
# 백엔드 (실 LLM): backend/.env 에 UPSTAGE_API_KEY (gitignored, 절대 커밋 금지)
cd backend && ROOMPILOT_PROVIDER=upstage uvicorn app.main:app --port 8000
# 입지 공공데이터 재수집(네트워크 필요, 4건 ~30초): geo_cache.json 갱신
cd backend && PYTHONPATH=. python3 scripts/enrich_listings.py
# 백엔드 4게이트 (도구는 ~/.local/bin)
python3 -m ruff check . && python3 -m mypy && python3 -m pytest -q && python3 -m compileall -q app tests demo.py chat.py scripts
# 프론트엔드 (WSL polling 적용됨 → 저장 시 자동 HMR)
cd frontend && npm run dev   # :5173, base=/asm-team10-ai-study/
# 프론트 4게이트
npm run lint && npx tsc --noEmit && npm run test && npm run build
# leaflet 설치는 --legacy-peer-deps 필요(eslint-plugin-react 피어 충돌)
```

## 함정 (학습된 것 — 반복 금지)

- `python` 없음 → **`python3`**. ruff/mypy/pytest 는 `~/.local/bin`
- 서버는 **harness `run_in_background:true`** 로. `pkill -f uvicorn` 금지(셸 자살). 종료는 `ss -ltnp` 로 PID 찾아 kill
- `with_structured_output(dict)` 는 스키마에 top-level `title` 필요
- `.env` gitignored, API 키 echo/커밋 금지. **main 직접 push 금지** → feature 브랜치 → PR(항상 Reviewer가 생성)
- **WSL `/mnt/e`는 inotify 미지원** → vite `server.watch.usePolling:true` 없으면 HMR 자동반영 안 됨
- **httpx 헤더는 ASCII만** → User-Agent에 한글 넣으면 UnicodeEncodeError (osm.py 참고)
- **Overpass 429 빈발** → 미러 순회 + 백오프 재시도(`_overpass_post`), 호출 간 sleep
- **OSM 미수록 데이터(가로등 등)는 "없음/적음"으로 단정 금지** → "확인 필요"로 분기(환각 방지)
- **geo_cache.json 은 점수화에도 영향** → 재수집 시 랭킹이 바뀔 수 있음. 시나리오 테스트는 캐시값 기준
- npm install 은 **`--legacy-peer-deps`** (eslint-plugin-react vs eslint10 피어 충돌)
- 핸드오프 파일: 디스크 `handoff.md` / git `HANDOFF.md` (드라이브 대소문자 무시 = 동일 파일)
- frontend 컴포넌트 규칙: 300줄↑ 분리검토, store에 UI 로직 금지(`frontend/CLAUDE.md`)

## 다음 할 일 (TODO)

1. **[최우선] 미커밋 변경 논리 단위 커밋 → PR** (Reviewer 게이트 후). 변경량 큼:
   - UI 리디자인 / 지도+상세모달 / 입지 공공데이터 / vite polling 등으로 분리 권장.
2. (선택) **data.go.kr 공공데이터** 연동 — 국토부 전월세 실거래가 등. **서비스키 필요**(사용자 발급).
   현재는 키 불필요한 OSM 스택만 사용 중.
3. (선택) 입지 `aiComment`를 실측 facts 기반으로 **LLM 생성**(현재는 결정적 요약문).
4. (선택) 매물 인벤토리·좌표를 실주소 기반으로 교체(현재 가격·좌표는 데모용, 좌표 *주변* 입지만 실데이터).

## 링크

- 레포: https://github.com/zxc88kr/asm-team10-ai-study
- FE 배포(main push 시 자동): https://zxc88kr.github.io/asm-team10-ai-study/
