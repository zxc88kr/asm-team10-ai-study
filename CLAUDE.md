# RoomPilot — Claude Code 가이드

## 프로젝트 구조

```
frontend/          React + Vite + Zustand + Tailwind CSS v4
  src/
    components/    UI 컴포넌트 (JSX)
    data/          시드 데이터 + 비즈니스 로직 (conditions, listings, scenario)
    store/         Zustand 상태 관리 (useAppStore.js)
backend/           미구현 (향후 FastAPI + LangGraph)
```

## 개발 명령어

```bash
# frontend/ 디렉토리에서 실행
npm run dev          # 개발 서버 (http://localhost:5173)
npm run build        # 프로덕션 빌드 → dist/
npm run test         # Vitest 전체 테스트 실행
npm run test:watch   # 테스트 watch 모드
npm run test:coverage # 커버리지 포함 실행
npm run lint         # ESLint (src/ 대상)
npm run format       # Prettier (src/ 대상)
```

## 컨벤션

- 언어: JavaScript (JSX), TypeScript 미사용
- 스타일: Tailwind CSS v4 + CSS 변수 (`index.css`의 `--blue`, `--ink` 등)
- 상태: Zustand (`useAppStore`) — 전역 단일 스토어
- 테스트: Vitest + React Testing Library, 테스트 파일은 `__tests__/` 폴더에 배치

## 금지사항

- `assets/css/`, `assets/js/` 파일 수정 금지 (레거시, 미사용)
- `dist/` 직접 수정 금지 (`npm run build`로 생성)
- `node_modules/` 직접 수정 금지

## 테스트 작성 원칙

- 비즈니스 로직 (`data/`, `store/`) 우선 테스트
- 컴포넌트는 렌더링 + 주요 인터랙션만 테스트
- Zustand store는 `reset()`으로 각 테스트 전 초기화

## 배포

GitHub Actions (`deploy-pages.yml`) — main 브랜치 push 시 자동 빌드·배포
배포 URL: `https://<owner>.github.io/asm-team10-ai-study/`
