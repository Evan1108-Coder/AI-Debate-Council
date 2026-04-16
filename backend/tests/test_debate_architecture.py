from pathlib import Path
import asyncio
from tempfile import TemporaryDirectory
import unittest

from backend.app.database import Database
from backend.app.debate import DebateManager
from backend.app.model_registry import MOCK_MODEL


class DebateArchitectureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "test.db")
        self.db.init()
        self.manager = DebateManager(self.db)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_active_agents_follow_debaters_per_team(self) -> None:
        session = self.db.create_session(max_sessions=10)
        settings = self.db.update_session_settings(session["id"], {"debaters_per_team": 4})

        agents = self.manager._active_debate_agents(settings)

        self.assertEqual(len(agents), 8)
        self.assertIn("pro_cross_examiner", {agent["role"] for agent in agents})
        self.assertIn("con_cross_examiner", {agent["role"] for agent in agents})

    def test_assignments_include_optional_judge_assistant(self) -> None:
        session = self.db.create_session(max_sessions=10)
        settings = self.db.update_session_settings(
            session["id"], {"debaters_per_team": 1, "judge_assistant_enabled": False}
        )

        assignments = self.manager._assignment_payload(settings, MOCK_MODEL)

        self.assertEqual([assignment["speaker"] for assignment in assignments], [
            "Pro Lead Advocate",
            "Con Lead Advocate",
            "Judge",
        ])

    def test_turn_bid_opens_pro_then_con(self) -> None:
        session = self.db.create_session(max_sessions=10)
        settings = self.db.get_session_settings(session["id"])
        agents = self.manager._active_debate_agents(settings)

        first = asyncio.run(
            self.manager._select_turn_bid(
                topic="Should cities ban private cars downtown?",
                agents=agents,
                transcript=[],
                turn_index=0,
                max_turns=6,
                model=MOCK_MODEL,
                session_settings=settings,
            )
        )
        second = asyncio.run(
            self.manager._select_turn_bid(
                topic="Should cities ban private cars downtown?",
                agents=agents,
                transcript=[
                    {
                        "role": first["agent"]["role"],
                        "speaker": first["agent"]["speaker"],
                        "team": first["agent"]["team"],
                        "content": "The Pro side opens.",
                    }
                ],
                turn_index=1,
                max_turns=6,
                model=MOCK_MODEL,
                session_settings=settings,
            )
        )

        self.assertEqual(first["agent"]["role"], "pro_lead_advocate")
        self.assertEqual(second["agent"]["role"], "con_lead_advocate")

    def test_intent_router_respects_explicit_debate_and_plain_chat(self) -> None:
        self.assertEqual(
            self.manager._heuristic_intent("Please debate whether schools should use AI tutors."),
            "debate",
        )
        self.assertEqual(
            self.manager._heuristic_intent("Can you tell me how to start the program?"),
            "chat",
        )
        self.assertEqual(
            self.manager._heuristic_intent("Can you tell me whether I should use port 6001?"),
            "chat",
        )

    def test_council_assistant_always_on_setting_is_detected(self) -> None:
        session = self.db.create_session(max_sessions=10)
        settings = self.db.update_session_settings(
            session["id"],
            {"agent_settings": {"council_assistant": {"always_on": True}}},
        )

        self.assertTrue(self.manager._council_assistant_always_on(settings))

    def test_debater_prompt_prefers_direct_in_room_address(self) -> None:
        session = self.db.create_session(max_sessions=10)
        settings = self.db.get_session_settings(session["id"])
        agent = next(
            item
            for item in self.manager._active_debate_agents(settings)
            if item["role"] == "con_rebuttal_critic"
        )
        transcript = [
            {
                "speaker": "Pro Lead Advocate",
                "role": "pro_lead_advocate",
                "team": "pro",
                "round": 1,
                "model": "mock-model",
                "content": "Polite prompts improve cooperation.",
            }
        ]
        bid = self.manager._bid(
            agent,
            0.8,
            "rebut the latest claim",
            "Polite prompts improve cooperation.",
            "the prior claim needs direct rebuttal",
        )

        messages = self.manager._agent_messages(
            "Should users be polite to AI?",
            agent,
            1,
            transcript,
            settings,
            self.manager._agent_generation_settings(settings, agent["archetype"]),
            bid,
        )
        prompt_text = "\n".join(message["content"] for message in messages)

        self.assertIn("Pro Lead Advocate, you said", prompt_text)
        self.assertIn('do not say "my opponent"', prompt_text.lower())


if __name__ == "__main__":
    unittest.main()
