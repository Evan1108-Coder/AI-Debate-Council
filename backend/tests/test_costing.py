import unittest

from backend.app.costing import CostTracker, estimate_tokens, normalize_currency


class CostingTests(unittest.TestCase):
    def test_cost_tracker_groups_models_and_converts_currency(self) -> None:
        tracker = CostTracker()
        tracker.record_call(
            model_name="gpt-4o-mini",
            input_text="hello world",
            output_text="a short answer",
            operation="Council Assistant",
        )
        tracker.record_call(
            model_name="gpt-4o-mini",
            input_text="more context",
            output_text="another answer",
            operation="Council Assistant",
        )

        summary = tracker.summary("CNY")

        self.assertEqual(summary["currency"], "CNY")
        self.assertEqual(summary["calls"], 2)
        self.assertEqual(len(summary["models"]), 1)
        self.assertGreater(summary["total"], 0)

    def test_estimate_tokens_and_currency_normalization(self) -> None:
        self.assertGreaterEqual(estimate_tokens("Denying oneself"), 2)
        self.assertEqual(normalize_currency("sgp"), "SGP")
        self.assertEqual(normalize_currency("bad"), "USD")


if __name__ == "__main__":
    unittest.main()
