# RoomPilot — AI 주거 코치 (프로토타입)

> 첫 독립 청년의 **말로 표현 못 한 생활 니즈**를 LLM이 집 조건으로 **번역·발굴**해, 근거와 함께 매물을 추천하는 멀티 에이전트 — 소마(SW마에스트로) 10조.

**▶ 라이브 데모:** https://zxc88kr.github.io/asm-team10-ai-study/

---

## 핵심 차별점

기존 부동산 검색은 **태그/필터 기반**이라 *사용자가 무엇이 중요한지 이미 안다*고 가정합니다. 하지만 첫 독립자의 진짜 문제는 **“무엇을 필터로 걸어야 할지조차 모른다”**는 것.

RoomPilot은 **대화**로 생활을 듣고, 사용자가 말하지 않은 조건까지 **발굴**해 보여줍니다.

| | 기존 태그 검색 | RoomPilot |
|---|---|---|
| 입력 | 내가 아는 필터만 체크 | 생활을 말하면 조건을 **발굴** |
| 조건 처리 | 모두 동급 ON/OFF, 하나 틀리면 제외 | 하드/소프트 + 가중치 → **트레이드오프** |
| 매물 매칭 | 태그 필드 일치 | 설명 텍스트의 **의미**까지 매칭 |
| 입지 | 누구에게나 같은 정보 | **이 사람 생활 기준**으로 해석 |
| 신뢰 | 결과만(블랙박스) | **카드·근거**가 보이고 수정 가능 |

---

## 이 프로토타입에서 볼 수 있는 것

1. **자라나는 조건 카드 인터뷰** — 대화하면 우측 ‘내 조건 요약’에 조건이 실시간으로 쌓입니다. 각 카드엔 *근거*와 *말함 / AI 발굴* 출처 표시.
2. **숨은 니즈 발굴 질문** — AI가 사용자가 말 안 한 생활 차원(귀가 안전, 환기 등)을 역으로 묻습니다.
3. **의미 기반 매칭 점수** — 매물 설명 텍스트에서 의미를 읽어 카드별 충족/부분/미흡을 판정하고 점수로 랭킹.
4. **맥락 기반 입지 해석** — ‘밤 11시 알바 귀가’ 같은 카드 기준으로 입지를 해석.
5. **루프백** — ‘조건 편집’으로 월세 상한을 올리면 추천이 즉시 갱신(트레이드오프 시연).
6. **차별점 지표** — 좌측 하단 ‘내가 말한 조건 vs AI가 발굴한 조건’ 카운터.

> 시나리오 주인공: **상경 대학 신입생(민지)**. 추천 답변 칩을 누르거나 직접 입력해 대화를 진행해 보세요.

---

## 실행 방법

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173/asm-team10-ai-study/
```

프로덕션 빌드:

```bash
cd frontend
npm run build   # frontend/dist/ 생성
npm run preview # 빌드 결과 로컬 확인
```

---

## 기술 구성

- **프론트엔드(이 레포):** React 19 + Vite 6 + Zustand + Tailwind CSS v4. `main` 푸시 시 GitHub Actions가 빌드 후 Pages 배포.
  - `src/data/` — 시드 매물·시나리오·조건 카드 정의
  - `src/store/useAppStore.js` — Zustand 스토어 (인터뷰 흐름·의미 매칭·루프백 로직)
  - `src/components/` — Sidebar, ChatPanel, ConditionSummary, RecommendationList, LocationAnalysis, ListingModal, Toast
- **전체 구현 목표(기획서):** React + FastAPI + **LangGraph** 오케스트레이션(Agent 1·2·3 + 사용자 승인 + 루프백) + **Claude API** 추론 + 지도·공공데이터. 이 프로토타입은 그 흐름을 시드 데이터·규칙으로 **재현한 프런트엔드 데모**입니다.

## 배포

`main` 브랜치 푸시 시 GitHub Actions(`.github/workflows/deploy-pages.yml`)가 `npm run build` 실행 후 `dist/`를 Pages에 자동 배포합니다.
