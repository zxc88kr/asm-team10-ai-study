# RoomPilot — Claude Code 가이드 (프로젝트 전체)

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
  - 테스트 작성
  ↓
[Reviewer Agent]
  - lint / typecheck / test / build — 4개 게이트 모두 통과 필수
  - 코드 리뷰 후 PR 생성
```

**규칙**
- 4개 게이트 중 하나라도 실패하면 Developer로 반환
- PR은 항상 Reviewer Agent가 생성, 사람이 직접 작성하지 않는다
- 커밋은 논리적 단위로 자율 분리한다 — 사람이 지시하지 않아도 작업 완료 시점에 스스로 커밋
- main 브랜치 직접 push 금지 — 반드시 feature 브랜치 → PR

## PR 형식

소제목은 `###` 사용, 이모티콘 배제.

```markdown
### Summary

- 변경 내용 항목 1
- 변경 내용 항목 2

### Test plan

- [ ] lint: 에러 0개
- [ ] tsc: 에러 0개
- [ ] test: N/N 통과
- [ ] build: 성공
```

## 프로젝트 구조

```
asm-team10-ai-study/
├── frontend/     React + Vite + Zustand + Tailwind CSS v4  (→ frontend/CLAUDE.md)
└── backend/      미구현 (향후 FastAPI + LangGraph)
```

## 배포

- FE 배포: `main` 브랜치 push 시 GitHub Actions(`deploy-pages.yml`)가 자동 빌드·배포
- CI: PR 생성 시 `ci.yml`이 lint + test 자동 실행
- 배포 URL: `https://zxc88kr.github.io/asm-team10-ai-study/`
