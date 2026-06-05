# Room Condition Agent

프론트엔드와 분리된 자취방 조건 추출 agent입니다.

## 역할

- 유저 채팅 메시지를 받는다.
- 하드 조건을 `위치/교통`, `월세`로 정리한다.
- 소프트 조건을 `편의 시설`, `벌레 여부`, `기본 옵션`, `반지하 여부`, `곰팡이`로 정리한다.
- 누적 조건 JSON과 다음 질문을 반환한다.

## 실행

```bash
cd backend
python3 agent_demo.py
```

## FastAPI 서버

설치:

```bash
cd backend
python3 -m pip install -r requirements.txt
```

실행:

```bash
uvicorn app:app --reload --port 8000
```

프론트에서 호출할 엔드포인트:

```http
POST http://localhost:8000/agent/message
```

요청:

```json
{
  "session_id": "user-1",
  "message": "강남역 근처 회사에 다니고 관리비 포함 월세 75만 원 이하였으면 좋겠어요."
}
```

응답은 `session_id`와 누적 조건 JSON을 최상위에 반환합니다.

```json
{
  "session_id": "user-1",
  "hard_conditions": {},
  "soft_conditions": {},
  "missing_required_conditions": [],
  "next_question": "..."
}
```

초기화:

```http
POST http://localhost:8000/agent/reset
```

## Upstage Agents API 연결

API 키는 코드에 넣지 말고 환경변수로 설정합니다.

```bash
export UPSTAGE_API_KEY="..."
export UPSTAGE_AGENT_ID="..."
```

로컬 개발에서는 `backend/.env`에 넣어도 됩니다. `.env`는 git ignore 대상입니다.
`UPSTAGE_AGENT_ID`는 Upstage Studio에서 Agent를 만든 뒤에만 넣습니다. 값이 없으면 `solar-pro3` chat 모델로 JSON 추출을 수행합니다.

사용 예:

```python
from agent import RoomConditionAgent

agent = RoomConditionAgent(use_solar=True)
state = agent.handle_message("강남역 근처, 관리비 포함 월세 75 이하였으면 좋겠어요.")
print(state)
```

키가 없거나 Solar 호출이 실패하면 rule 기반 추출로 fallback합니다.
