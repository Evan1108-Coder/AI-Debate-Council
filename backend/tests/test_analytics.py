import unittest
import json

from backend.app.analytics import analyze_debate, format_analytics_report


class DebateAnalyticsTests(unittest.TestCase):
    def test_analysis_combines_multiple_ai_methods(self) -> None:
        transcript = [
            {
                "speaker": "Advocate",
                "role": "advocate",
                "round": 1,
                "model": "gpt-4o",
                "content": "Cities should add car-free zones because evidence shows cleaner air and safer streets.",
            },
            {
                "speaker": "Critic",
                "role": "critic",
                "round": 1,
                "model": "gpt-4o",
                "content": "However, the policy has a risk: delivery costs could rise unless transit improves.",
            },
            {
                "speaker": "Researcher",
                "role": "researcher",
                "round": 2,
                "model": "gpt-4o",
                "content": "The data is mixed. Studies should measure business revenue, air quality, and access.",
            },
        ]

        analysis = analyze_debate("Should cities ban private cars downtown?", transcript)

        self.assertEqual(analysis["turn_count"], 3)
        self.assertIn(analysis["ensemble"]["weighted_vote"], {"support", "oppose", "mixed"})
        self.assertAlmostEqual(sum(analysis["bayesian"]["probabilities"].values()), 1.0, places=2)
        self.assertGreaterEqual(analysis["argument_graph"]["node_count"], 3)
        self.assertGreaterEqual(len(analysis["attention"]["top_terms"]), 1)
        self.assertIn("lead_expert", analysis["mixture_of_experts"])

    def test_analytics_report_is_judge_prompt_ready(self) -> None:
        analysis = analyze_debate(
            "Should teams use AI code review?",
            [
                {
                    "speaker": "Advocate",
                    "role": "advocate",
                    "round": 1,
                    "model": "gpt-4o",
                    "content": "Teams should use AI review because it catches common defects quickly.",
                }
            ],
        )

        report = format_analytics_report(analysis)

        self.assertIn("Ensemble majority vote", report)
        self.assertIn("Bayesian probabilities", report)
        self.assertIn("Argument graph", report)

    def test_side_based_roles_have_side_bias(self) -> None:
        analysis = analyze_debate(
            "Should cities ban private cars downtown?",
            [
                {
                    "speaker": "Pro Lead Advocate",
                    "role": "pro_lead_advocate",
                    "round": 1,
                    "model": "minimax-m2.7",
                    "content": "This policy should improve air quality because it reduces traffic.",
                },
                {
                    "speaker": "Con Rebuttal Critic",
                    "role": "con_rebuttal_critic",
                    "round": 1,
                    "model": "minimax-m2.7",
                    "content": "I disagree because the risk to access and small businesses is serious.",
                },
            ],
        )

        self.assertEqual(analysis["stance"]["by_role"]["Pro Lead Advocate"], "support")
        self.assertEqual(analysis["stance"]["by_role"]["Con Rebuttal Critic"], "oppose")

    def test_moe_weights_only_include_active_roles(self) -> None:
        analysis = analyze_debate(
            "Should cities ban private cars downtown?",
            [
                {
                    "speaker": "Pro Lead Advocate",
                    "role": "pro_lead_advocate",
                    "round": 1,
                    "model": "minimax-m2.7",
                    "content": "The city should reduce cars because safer streets are valuable.",
                },
                {
                    "speaker": "Con Rebuttal Critic",
                    "role": "con_rebuttal_critic",
                    "round": 1,
                    "model": "minimax-m2.7",
                    "content": "However, access risk is serious unless transit improves.",
                },
            ],
        )

        role_weights = analysis["mixture_of_experts"]["role_weights"]
        self.assertEqual(set(role_weights), {"pro_lead_advocate", "con_rebuttal_critic"})
        self.assertNotIn("evidence_researcher", role_weights)
        self.assertNotIn("cross_examiner", role_weights)

    def test_argument_graph_is_json_serializable(self) -> None:
        analysis = analyze_debate(
            "Should schools ban phones?",
            [
                {
                    "speaker": "Pro Lead Advocate",
                    "role": "pro_lead_advocate",
                    "round": 1,
                    "model": "gpt-4o-mini",
                    "content": "Schools should ban phones because attention and classroom evidence improve.",
                },
                {
                    "speaker": "Con Lead Advocate",
                    "role": "con_lead_advocate",
                    "round": 1,
                    "model": "gpt-4o-mini",
                    "content": "Schools should not ban phones because safety and family contact matter.",
                },
            ],
        )

        json.dumps(analysis["argument_graph"])


if __name__ == "__main__":
    unittest.main()
