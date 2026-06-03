# Frontend Claude 가이드 (Monorepo 전용)

이 문서는 `/frontend` 작업에만 적용된다. 루트 `CLAUDE.md`의 공통 원칙을 따르되, 구현·리뷰 기준은 FE 맥락에서 아래 규칙을 우선 적용한다.

## Monorepo 작업 경계

- FE 작업은 기본적으로 `/frontend` 하위 파일에서 완료한다.
- 루트 문서/설정 변경이 필요할 때만 루트 파일을 수정하고, 변경 이유를 PR 설명에 명시한다.
- `/backend` 변경이 필요한 요구사항은 별도 브랜치 또는 별도 PR로 분리한다.

## Code Quality Rules

### 1) Commit Gate (커밋 전 필수)

`/frontend`에서 아래 게이트를 모두 통과한 뒤 커밋한다.

```bash
npm run lint
npx tsc --noEmit
npm run test
npm run build
```

### 2) 기준

#### File
- 파일 하나는 하나의 책임만 가진다.
- 기능 구현과 문서 수정은 같은 커밋에 섞지 않는다.
- 신규 파일 추가 시 기존 폴더 규칙(`components/`, `store/`, `data/`)을 따른다.

#### Function
- 함수는 한 가지 동작만 수행하고 이름으로 의도를 설명해야 한다.
- 입력/출력 타입을 명확히 하고, 가능한 순수 함수 형태를 우선한다.
- 예외 케이스(빈 값, 범위 초과, null/undefined)를 명시적으로 처리한다.

#### Component
- UI 표현과 상태 변경 로직을 분리한다.
- props 타입을 명확히 선언하고, 파생 상태는 중복 저장하지 않는다.
- 부수효과는 `useEffect`에서 최소화하고 정리(cleanup)를 보장한다.

#### Store
- Zustand store는 상태(state)와 액션(action) 책임을 분리한다.
- 액션은 예측 가능해야 하며, 테스트 가능한 단위로 유지한다.
- 스토어 변경 시 관련 테스트(`src/store/__tests__`)를 함께 점검한다.

#### Service (data/domain)
- `src/data`의 도메인 로직은 UI와 분리된 상태로 유지한다.
- 하드코딩된 매직값은 상수 또는 타입으로 의미를 드러낸다.
- 점수/추천 규칙 변경 시 기존 시나리오 테스트를 함께 확인한다.

### 3) Review 체크리스트

- [ ] 변경 범위가 FE 요구사항에만 한정되어 있는가?
- [ ] 커밋 목적(`fix/docs/refactor/test`)이 단일하며 브랜치 목적과 일치하는가?
- [ ] lint / type-check / test / build 게이트를 모두 통과했는가?
- [ ] 상태/도메인 로직 변경에 대한 테스트가 존재하거나 기존 테스트가 충분한가?
- [ ] PR 설명에 변경 이유와 검증 방법이 명확히 기록되었는가?
