# RoomPilot — Claude Code 가이드

## 개발 워크플로우

모든 기능 개발은 아래 3-에이전트 워크플로우를 따른다.

```
사용자 요청
  ↓
[Planner Agent]
  - 요구사항 분석
  - GitHub Issue 생성 (제목·설명·acceptance criteria)
  - feature 브랜치명 결정 (feat/<scope>)
  ↓
[Developer Agent]
  - feature 브랜치 생성
  - 구현
  - 테스트 작성 (__tests__/ 에 배치)
  ↓
[Reviewer Agent]
  - npm run lint       (ESLint — 에러 0개 필수)
  - npx tsc --noEmit   (TypeScript — 에러 0개 필수)
  - npm run test       (Vitest — 전체 통과 필수)
  - npm run build      (Vite 빌드 성공 필수)
  - 코드 리뷰 (버그·타입·테스트 누락 체크)
  - PR 생성 (제목·summary·test plan 포함)
```

**규칙**
- Reviewer 4개 게이트(lint/tsc/test/build) 중 하나라도 실패하면 Developer로 반환
- PR은 항상 Reviewer Agent가 생성, 사람이 직접 작성하지 않는다
- 각 커밋은 역할 단위로 분리: 하네스·구현·마이그레이션 등

---

## 프로젝트 구조

```
frontend/          React + Vite + Zustand + Tailwind CSS v4
  src/
    types.ts       공유 타입 정의 (Listing, ConditionCard, ScoredListing 등)
    components/    UI 컴포넌트 (.tsx)
    data/          시드 데이터 + 비즈니스 로직 (.ts)
    store/         Zustand 상태 관리 (useAppStore.ts)
backend/           미구현 (향후 FastAPI + LangGraph)
```

## 개발 명령어

```bash
# frontend/ 디렉토리에서 실행
npm run dev           # 개발 서버 (http://localhost:5173)
npm run build         # 프로덕션 빌드 → dist/
npm run test          # Vitest 전체 테스트 실행
npm run test:watch    # 테스트 watch 모드
npm run test:coverage # 커버리지 포함 실행
npm run lint          # ESLint (src/ 대상)
npm run format        # Prettier (src/ 대상)
npx tsc --noEmit      # TypeScript 타입 체크
```

## 컨벤션

- 언어: TypeScript (strict 모드), JSX → TSX
- 타입: 공유 타입은 `src/types.ts`에 정의, 컴포넌트 props는 해당 파일 내 interface
- 스타일: Tailwind CSS v4 + CSS 변수 (`index.css`의 `--blue`, `--ink` 등)
- 상태: Zustand (`useAppStore`) — 전역 단일 스토어
- 테스트: Vitest + React Testing Library, 테스트 파일은 `__tests__/` 폴더에 배치

## 금지사항

- `assets/css/`, `assets/js/` 파일 수정 금지 (레거시, 미사용)
- `dist/` 직접 수정 금지 (`npm run build`로 생성)
- `node_modules/` 직접 수정 금지
- main 브랜치 직접 push 금지 — 반드시 feature 브랜치 → PR

## 테스트 작성 원칙

- 비즈니스 로직 (`data/`, `store/`) 우선 테스트
- 컴포넌트는 렌더링 + 주요 인터랙션만 테스트
- Zustand store는 `reset()`으로 각 테스트 전 초기화

## 배포

GitHub Actions (`deploy-pages.yml`) — main 브랜치 push 시 자동 빌드·배포
CI (`ci.yml`) — PR 생성 시 lint + test 자동 실행
배포 URL: `https://<owner>.github.io/asm-team10-ai-study/`
