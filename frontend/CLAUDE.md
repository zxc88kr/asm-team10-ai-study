# RoomPilot Frontend — Claude Code 가이드

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

## 구조

```
src/
  types.ts       공유 타입 정의 (Listing, ConditionCard, ScoredListing 등)
  components/    UI 컴포넌트 (.tsx)
  data/          시드 데이터 + 비즈니스 로직 (.ts)
  store/         Zustand 상태 관리 (useAppStore.ts)
```

## 컨벤션

- 언어: TypeScript (strict 모드), JSX → TSX
- 타입: 공유 타입은 `src/types.ts`에 정의, 컴포넌트 props는 해당 파일 내 `interface`
- 스타일: Tailwind CSS v4 + CSS 변수 (`index.css`의 `--blue`, `--ink` 등)
- 상태: Zustand (`useAppStore`) — 전역 단일 스토어

## 테스트

- 테스트 파일은 대상 파일과 같은 디렉토리의 `__tests__/` 폴더에 배치
- 비즈니스 로직 (`data/`, `store/`) 우선 테스트
- 컴포넌트는 렌더링 + 주요 인터랙션만 테스트
- Zustand store는 `reset()`으로 각 테스트 전 초기화

## 금지사항

- `assets/css/`, `assets/js/` 수정 금지 (레거시, 미사용)
- `dist/` 직접 수정 금지 (`npm run build`로 생성)
- `node_modules/` 직접 수정 금지

---

# Code Quality Rules

## Commit

커밋 전 필수 게이트 — 하나라도 실패 시 커밋 불가

```bash
npm run lint       # 에러 0개
npx tsc --noEmit   # 에러 0개
npm run test       # 전체 통과
npm run build      # 빌드 성공
```

커밋은 논리적 단위로 자동 분리한다. 사람이 지시하지 않아도 작업 완료 시점에 스스로 커밋한다.

## File

| 기준 | 조치 |
|---|---|
| 300줄 이상 | 분리 검토 |
| 500줄 이상 | 분리 필수 |

## Function

| 기준 | 조치 |
|---|---|
| 30줄 이상 | 분리 검토 |
| 50줄 이상 | 분리 필수 |

## Component

- 하나의 컴포넌트는 하나의 책임만 가진다
- 렌더링 로직과 비즈니스 로직을 섞지 않는다
- props drilling이 2단계를 초과하면 구조 재검토

## Store (`useAppStore.ts`)

- UI 로직 금지 (className 계산, DOM 조작 등)
- 순수한 상태·액션·파생 데이터만 포함
- 컴포넌트별 로컬 상태는 `useState`로 분리

## Service / 유틸 함수 (`data/`, 순수 로직)

- React Hook 사용 금지
- 컴포넌트에 의존하지 않는 순수 함수로 작성
- 단위 테스트 필수

## Review 체크리스트

PR 생성 전 아래 항목을 확인한다.

- [ ] 중복 코드 — 동일 로직이 2곳 이상이면 추출
- [ ] 긴 함수 — 30줄 초과 함수 존재 여부
- [ ] 긴 컴포넌트 — 300줄 초과 파일 존재 여부
- [ ] 테스트 누락 — 새 비즈니스 로직에 테스트 없는 경우
- [ ] `any` 사용 — TypeScript `any` 타입 사용 여부
