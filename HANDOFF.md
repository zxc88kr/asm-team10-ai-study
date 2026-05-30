# HANDOFF — RoomPilot (소마 10조) 세션 인수인계

> 마지막 작업일: 2026-05-30
> 다음 세션에서 이 파일만 읽으면 바로 이어갈 수 있도록 정리한 문서.

---

## 0. 한 줄 요약

**RoomPilot** — 첫 독립 청년의 *말로 표현 못 한 생활 니즈*를 LLM이 집 조건으로 **번역·발굴**해 근거와 함께 매물을 추천하는 멀티 에이전트. 기존 부동산의 **태그 검색 → LLM 의미 이해 추천**으로의 전환이 핵심 차별점.

이번 세션에서 한 일: **브레인스토밍 → 기획서(docx) 작성 → 시각자료 3종 → 정적 프로토타입(GitHub Pages) 구축 → 배포(소유자 토글 1개 남음)**.

---

## 1. 확정된 기획 의사결정 (브레인스토밍 결과)

- **차별화 핵심:** 라이프스타일 → 집 조건 **번역/발굴** ("내가 몰랐던 내 조건을 찾아준다")
- **데모 페르소나:** 상경한 지방 **대학 신입생**(김민지). 저예산·학교근처·안전·첫 자취
- **인터랙션 척추:** **A(자라나는 조건 카드)** + **C(숨은 니즈 발굴 질문)** 결합
- **에이전트 3종:** ① 니즈 통역사(A+C) → ② 매물 큐레이터(의미 매칭·점수) → ③ 입지 해설사(맥락 해석), + **루프백**(카드 수정 시 2·3 재실행)
- **공용 인터페이스:** `니즈 프로파일` = 하드 제약(예산 등) + 소프트 카드(중요도 가중치) → 트레이드오프 가능 추천
- **LLM 구동(실제 목표):** 절충 — 오케스트레이션·툴은 로컬, LLM 추론만 API(Claude)
- **매물 데이터(실제 목표):** LLM으로 가상 매물 생성 + 사람 검수
- **UI:** 3-패널 (좌 워크플로우 스텝 / 중앙 AI 채팅 / 우 조건요약·추천TOP3·입지) — 참고 UI 이미지 반영

---

## 2. 산출물 위치

### 기획 문서 (작업 루트: `/mnt/c/dev/2026 soma_ai_home/`)
- `[10조]프로젝트 기획서_RoomPilot.docx` — **제출용 기획서** (양식 5섹션 + 차별점표 + 그림 3개 삽입)
- `[10조]프로젝트 기획서 양식_(10조)_(주제).docx` — 원본 빈 템플릿 (손대지 않음)
- `docs/superpowers/specs/2026-05-30-roompilot-design.md` — 설계 문서(상세)
- `docs/images/{architecture,flowchart,ui_mockup}.png` — 시각자료 3종
- `build_proposal.py` — 기획서 docx 재생성 스크립트
- `build_images.py` — 이미지 3종 재생성 스크립트 (Malgun Gothic 사용)

### 프로토타입 (git 레포: `asm-team10-ai-study/`)
- `index.html` — 3-패널 셸
- `assets/css/styles.css` — 스타일
- `assets/js/data.js` — **시드 매물 6건 + 시나리오 + 조건 카드 정의** (여기가 데이터/로직의 핵심)
- `assets/js/app.js` — 인터뷰 흐름·의미 매칭·입지·루프백·모달
- `.github/workflows/deploy-pages.yml` — Pages 배포 워크플로
- `README.md` — 프로젝트 소개·실행법

---

## 3. ⚠️ 프로토타입은 "목 데이터 + 규칙 기반"임 (실제 LLM 미연결)

GitHub Pages는 정적 호스팅이라 백엔드/LLM 실행 불가 → **에이전트 흐름을 재현한 프런트엔드 데모**.

| 에이전트 | 지금 상태 | 코드 위치 |
|---|---|---|
| Agent 1 (니즈 통역사) | 대화·질문·생성 카드가 **스크립트(대본)** | `data.js`의 `SCENARIO` |
| Agent 2 (매물 큐레이터) | 설명 텍스트 **키워드 스캔** 규칙 매칭, 매물은 시드 6건 | `data.js`의 `CONDITION_CARDS[].match()`, `LISTINGS` |
| Agent 3 (입지 해설사) | 매물 필드로 **공식 계산** (지도 API 없음) | `app.js`의 `renderLocation()` |

→ 사용자가 자유 문장을 치면 진짜 이해하는 게 아니라, **추천 답변 칩**을 누르는 시나리오로 동작.

---

## 4. 배포 현황 & 막힌 지점 (중요)

- **레포:** https://github.com/zxc88kr/asm-team10-ai-study (owner: **zxc88kr**, public)
- **브랜치:** `main`, `proto/05.30` — 둘 다 최신 커밋 `55c0a07`
- **커밋 이력:** `d2effd5`(프로토타입) → `3f1efc2`(워크플로 enablement 제거) → `55c0a07`(모달 hidden 버그 수정)
- **Pages URL(활성화 후):** **https://zxc88kr.github.io/asm-team10-ai-study/**

### 🔴 남은 단 하나: 소유자가 Pages 토글을 켜야 함
- 현재 git 인증 계정은 **`sionhyeop`** (이 레포 권한 `admin:false, push:true`).
  → push는 되지만 **Pages 활성화·설정 변경 API는 403/404**. admin이 아니라서 막힘.
- **소유자 `zxc88kr` 계정으로** 아래를 1회 수행하면 즉시 배포됨:
  1. 레포 → **Settings** → 좌측 **Pages**
  2. **Build and deployment → Source: `Deploy from a branch`**
  3. Branch **`main`** / 폴더 **`/ (root)`** → **Save**
  4. 1~2분 후 위 Pages URL 접속
- (대안) 소유자가 `sionhyeop`을 **Admin**으로 승격하거나 zxc88kr 토큰을 git에 인증해주면, 다음 세션에서 **API로 활성화까지 자동 처리 가능.**
- Actions 워크플로 방식을 쓰려면 Source에서 `GitHub Actions` 선택 (그러면 push마다 자동 배포). 단 `Deploy from a branch`가 더 단순.

---

## 5. 로컬 실행 / 미리보기

```bash
cd "/mnt/c/dev/2026 soma_ai_home/asm-team10-ai-study"
python3 -m http.server 8000
# 브라우저: http://localhost:8000   (localhost 거부 시 WSL IP: http://<wsl-ip>:8000)
```
- WSL IP 확인: `hostname -I | awk '{print $1}'` (이전 세션 값 172.29.233.125 — 재부팅 시 바뀔 수 있음)
- 서버는 세션이 살아있는 동안만 동작.

### 검증 방법 (헤드리스)
- Chromium은 WSL 시스템 라이브러리 부족으로 실행 불가 → **jsdom**으로 흐름 검증함.
- 검증 스크립트 위치: `/tmp/uitest/test.mjs` (jsdom 설치됨). 전 흐름 통과(런타임 에러 0).
  *(재실행: `cd /tmp/uitest && node test.mjs`)*

---

## 6. 다음에 할 일 (우선순위 후보)

1. **🔴 Pages 활성화** — 소유자 토글 (4번 참고). 끝나면 URL 정상 확인.
2. **실제 에이전트 백엔드 연결** (원래 목표 "로컬 Agentic Workflow 데모"):
   - FastAPI + **LangGraph**(Agent 1·2·3 + 사용자 승인 노드 + 루프백) + **Claude API** 추론
   - 자유 문장 → 진짜 조건 추출/발굴/의미매칭. 키는 서버 환경변수.
   - 프런트는 현재 UI 재사용, 데이터/매칭만 API 호출로 교체 (`data.js`/`app.js`의 목 부분 대체)
3. **기획서 docx 최종 검토** — 색감/문구/분량, 학교명 `○○대` placeholder를 특정 대학으로 고정 권장.
4. (선택) 시드 매물 확장, 입지에 실제 지도/공공데이터 API 부분 연결.

---

## 7. 환경 메모 (다음 세션 빠른 시작용)

- 작업 루트: `/mnt/c/dev/2026 soma_ai_home/` (경로에 공백 있음 — 따옴표 필수)
- **git 인증:** Windows Git Credential Manager 사용 (`credential.helper` = `/mnt/c/Program Files/Git/mingw64/bin/git-credential-manager.exe`). push 무인증 동작 확인됨.
- **`gh` CLI 없음.** GitHub 작업은 REST API(curl) + git으로 처리.
- **`uv` 있음** (`~/.local/bin/uv`) — python 패키지: `uv run --with python-docx python3 build_proposal.py`, `uv run --with matplotlib python3 build_images.py`
- **node 22 / npm 10** 있음. python3 있음(pip/ensurepip 없음 → uv 사용).
- 한글 폰트: `/mnt/c/Windows/Fonts/malgun.ttf` (matplotlib 다이어그램용)

### 자주 쓰는 명령
```bash
# 기획서/이미지 재생성
cd "/mnt/c/dev/2026 soma_ai_home"
~/.local/bin/uv run --with matplotlib python3 build_images.py
~/.local/bin/uv run --with python-docx python3 build_proposal.py

# 프로토타입 푸시 (proto/05.30 작업 → main 동기화)
cd "/mnt/c/dev/2026 soma_ai_home/asm-team10-ai-study"
git add -A && git commit -m "..."
git branch -f main HEAD
git push origin proto/05.30
git push origin proto/05.30:main   # main 푸시가 Pages 워크플로 트리거

# 현재 사용자 레포 권한 확인 (admin 여부)
TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null | sed -n 's/^password=//p')
curl -s -H "Authorization: Bearer $TOKEN" https://api.github.com/repos/zxc88kr/asm-team10-ai-study | node -e "let d='';process.stdin.on('data',c=>d+=c).on('end',()=>console.log(JSON.parse(d).permissions))"
```

---

## 8. 핵심 링크 모음

- 레포: https://github.com/zxc88kr/asm-team10-ai-study
- Pages(활성화 후): https://zxc88kr.github.io/asm-team10-ai-study/
- 로컬: http://localhost:8000
