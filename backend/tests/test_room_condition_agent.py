from __future__ import annotations

import unittest

from agent import RoomConditionAgent


class RoomConditionAgentTest(unittest.TestCase):
    def test_extracts_hard_conditions(self) -> None:
        agent = RoomConditionAgent(use_solar=False)

        agent.handle_message("강남역 근처 회사에 다녀요.")
        state = agent.handle_message("관리비 포함 75만 원 이하였으면 좋겠어요.")

        self.assertIn("강남역", state["hard_conditions"]["location_transport"]["landmarks"])
        self.assertEqual(state["hard_conditions"]["monthly_rent"]["max_manwon"], 75)
        self.assertTrue(state["hard_conditions"]["monthly_rent"]["includes_management_fee"])

    def test_extracts_soft_conditions(self) -> None:
        agent = RoomConditionAgent(use_solar=False)

        agent.handle_message("출퇴근은 35분 이내면 좋고 반지하는 싫어요.")
        state = agent.handle_message("벌레랑 곰팡이는 피하고 싶고 에어컨이랑 세탁기는 있었으면 해요.")

        self.assertEqual(state["hard_conditions"]["location_transport"]["commute_time_max_minutes"], 35)
        self.assertTrue(state["soft_conditions"]["basement"]["avoid"])
        self.assertTrue(state["soft_conditions"]["pests"]["avoid"])
        self.assertTrue(state["soft_conditions"]["mold"]["avoid"])
        self.assertIn("에어컨", state["soft_conditions"]["default_options"]["preferred"])
        self.assertIn("세탁기", state["soft_conditions"]["default_options"]["preferred"])

    def test_missing_required_conditions(self) -> None:
        agent = RoomConditionAgent(use_solar=False)

        state = agent.handle_message("벌레는 싫어요.")

        self.assertEqual(state["missing_required_conditions"], ["위치/교통", "월세"])
        self.assertIn("어느 지역", state["next_question"])

    def test_asks_soft_conditions_once_after_hard_conditions(self) -> None:
        agent = RoomConditionAgent(use_solar=False)

        agent.handle_message("강남역 근처 회사에 다녀요.")
        state = agent.handle_message("관리비 포함 75만 원 이하였으면 좋겠어요.")

        self.assertFalse(state["is_complete"])
        self.assertEqual(state["next_action"], "ask_soft_conditions")
        self.assertIn("편의 시설", state["next_question"])

    def test_completes_after_soft_condition_answer(self) -> None:
        agent = RoomConditionAgent(use_solar=False)

        agent.handle_message("강남역 근처 회사에 다녀요.")
        agent.handle_message("관리비 포함 75만 원 이하였으면 좋겠어요.")
        state = agent.handle_message("벌레가 없었으면 좋겠어")

        self.assertTrue(state["soft_conditions"]["pests"]["avoid"])
        self.assertTrue(state["is_complete"])
        self.assertEqual(state["next_action"], "recommend_listings")
        self.assertIn("추천", state["next_question"])

    def test_completes_when_user_has_no_more_soft_conditions(self) -> None:
        agent = RoomConditionAgent(use_solar=False)

        agent.handle_message("강남역 근처 회사에 다녀요.")
        agent.handle_message("관리비 포함 75만 원 이하였으면 좋겠어요.")
        state = agent.handle_message("그리곤 없어")

        self.assertTrue(state["is_complete"])
        self.assertEqual(state["next_action"], "recommend_listings")

    def test_completes_after_generic_facility_answer(self) -> None:
        agent = RoomConditionAgent(use_solar=False)

        agent.handle_message("강남역 근처 회사에 다녀요.")
        agent.handle_message("관리비 포함 75만 원 이하였으면 좋겠어요.")
        state = agent.handle_message("편의 시설이 주변에 많았으면 좋겠어")

        self.assertIn("편의 시설", state["soft_conditions"]["convenience_facilities"]["preferred"])
        self.assertTrue(state["is_complete"])
        self.assertEqual(state["next_action"], "recommend_listings")


if __name__ == "__main__":
    unittest.main()