from __future__ import annotations

import unittest


class ListingCuratorTest(unittest.TestCase):
    def _make_conditions(
        self,
        max_manwon: int = 70,
        avoid_basement: bool = True,
        avoid_pests: bool = True,
        avoid_mold: bool = True,
        options: list | None = None,
        facilities: list | None = None,
    ) -> dict:
        from agent.schema import create_empty_conditions
        state = create_empty_conditions()
        state["hard_conditions"]["monthly_rent"]["max_manwon"] = max_manwon
        state["hard_conditions"]["monthly_rent"]["max_krw"] = max_manwon * 10000
        state["soft_conditions"]["basement"]["avoid"] = avoid_basement
        state["soft_conditions"]["pests"]["avoid"] = avoid_pests
        state["soft_conditions"]["mold"]["avoid"] = avoid_mold
        if options:
            state["soft_conditions"]["default_options"]["preferred"] = options
        if facilities:
            state["soft_conditions"]["convenience_facilities"]["preferred"] = facilities
        return state

    def test_hard_filter_rent_ceiling(self) -> None:
        from agent import ListingCurator
        curator = ListingCurator(use_solar=False)
        conditions = self._make_conditions(max_manwon=50)
        result = curator.recommend(conditions, top_n=10)
        for prop in result["top_properties"]:
            self.assertLessEqual(prop["monthly_rent"], 50)

    def test_hard_filter_basement_excluded(self) -> None:
        from agent import ListingCurator
        curator = ListingCurator(use_solar=False)
        conditions = self._make_conditions(max_manwon=200)
        result = curator.recommend(conditions, top_n=10)
        ids = [p["property_id"] for p in result["top_properties"]]
        self.assertNotIn("P004", ids)

    def test_basement_included_when_not_avoided(self) -> None:
        from agent import ListingCurator
        curator = ListingCurator(use_solar=False)
        conditions = self._make_conditions(avoid_basement=False, max_manwon=40)
        result = curator.recommend(conditions, top_n=10)
        ids = [p["property_id"] for p in result["top_properties"]]
        self.assertIn("P004", ids)

    def test_top_n_respected(self) -> None:
        from agent import ListingCurator
        curator = ListingCurator(use_solar=False)
        conditions = self._make_conditions(max_manwon=200)
        result = curator.recommend(conditions, top_n=3)
        self.assertLessEqual(len(result["top_properties"]), 3)

    def test_results_sorted_by_score_desc(self) -> None:
        from agent import ListingCurator
        curator = ListingCurator(use_solar=False)
        conditions = self._make_conditions()
        result = curator.recommend(conditions, top_n=5)
        scores = [p["score"] for p in result["top_properties"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_hard_filter_passed_flag(self) -> None:
        from agent import ListingCurator
        curator = ListingCurator(use_solar=False)
        conditions = self._make_conditions()
        result = curator.recommend(conditions)
        for prop in result["top_properties"]:
            self.assertTrue(prop["hard_filter_passed"])

    def test_soft_card_matches_present(self) -> None:
        from agent import ListingCurator
        curator = ListingCurator(use_solar=False)
        conditions = self._make_conditions(options=["에어컨", "세탁기"])
        result = curator.recommend(conditions)
        for prop in result["top_properties"]:
            self.assertIsInstance(prop["soft_card_matches"], list)
            card_names = [m["card"] for m in prop["soft_card_matches"]]
            self.assertIn("default_options", card_names)

    def test_session_id_propagated(self) -> None:
        from agent import ListingCurator
        curator = ListingCurator(use_solar=False)
        conditions = self._make_conditions()
        result = curator.recommend(conditions, session_id="test-sess-1")
        self.assertEqual(result["session_id"], "test-sess-1")

    def test_agent_mode_is_rule_when_solar_off(self) -> None:
        from agent import ListingCurator
        curator = ListingCurator(use_solar=False)
        conditions = self._make_conditions()
        result = curator.recommend(conditions)
        for prop in result["top_properties"]:
            self.assertEqual(prop["agent_mode"], "rule")


if __name__ == "__main__":
    unittest.main()