from __future__ import annotations

import json

from agent import RoomConditionAgent


def main() -> None:
    agent = RoomConditionAgent(use_solar=False)
    sample_messages = [
        "강남역 근처 회사에 다녀요.",
        "관리비 포함 75만 원 이하였으면 좋겠어요.",
        "출퇴근은 35분 이내면 좋고 반지하는 싫어요.",
        "벌레랑 곰팡이는 피하고 싶고 에어컨이랑 세탁기는 있었으면 해요.",
    ]

    for message in sample_messages:
        state = agent.handle_message(message)

    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
