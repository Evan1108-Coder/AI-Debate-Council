from pathlib import Path
import asyncio
from tempfile import TemporaryDirectory
import unittest

from fastapi import WebSocketDisconnect

from backend.app.database import Database
from backend.app.debate import ClientDisconnectedError, DebateManager, StreamingSanitizer
from backend.app.model_registry import MOCK_MODEL
from backend.app.runtime_diary import runtime_diary


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
            "Pro Advocate",
            "Con Advocate",
            "Judge",
        ])

    def test_professional_flow_uses_advocate_led_discussions(self) -> None:
        session = self.db.create_session(max_sessions=10)
        settings = self.db.get_session_settings(session["id"])
        flow = self.manager._debate_flow(settings)

        self.assertEqual(flow[0]["agent"]["role"], "pro_lead_advocate")
        self.assertEqual(flow[1]["agent"]["role"], "con_rebuttal_critic")
        self.assertEqual(flow[2]["agent"]["role"], "con_lead_advocate")
        discussion_roles = [phase["agent"]["role"] for phase in flow if phase["kind"] == "discussion"]
        self.assertTrue(discussion_roles)
        self.assertTrue(all(role in {"pro_lead_advocate", "con_lead_advocate"} for role in discussion_roles))
        self.assertEqual(discussion_roles[0], "pro_lead_advocate")
        self.assertIn("con_lead_advocate", discussion_roles)

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
        self.assertEqual(
            self.manager._heuristic_intent("Which is better, morning ice cream or night ice cream?"),
            "debate",
        )

    def test_intent_router_does_not_treat_debate_word_as_command(self) -> None:
        session = self.db.create_session(max_sessions=10)
        settings = self.db.get_session_settings(session["id"])

        intent = asyncio.run(
            self.manager._classify_intent(
                "Why did it start a debate when I typed the word debate?",
                MOCK_MODEL,
                settings,
                session_id=session["id"],
            )
        )

        self.assertEqual(intent, "chat")

    def test_intent_response_parser_uses_json_intent_not_reason_keywords(self) -> None:
        self.assertEqual(
            self.manager._parse_intent_response(
                '{"intent":"chat","reason":"The user mentions debate but asks about a bug."}'
            ),
            "chat",
        )
        self.assertEqual(
            self.manager._parse_intent_response(
                '{"intent":"debate","reason":"The user asks the council to argue both sides."}'
            ),
            "debate",
        )

    def test_council_assistant_system_context_includes_architecture_and_diary(self) -> None:
        session = self.db.create_session(max_sessions=10)
        runtime_diary.record(
            "backend terminal",
            "test diary event",
            "Focused backend test event for Council Assistant context.",
            session_id=session["id"],
        )

        context = self.manager._system_context(session["id"])

        self.assertIn("FastAPI", context)
        self.assertIn("Next.js", context)
        self.assertIn("test diary event", context)
        self.assertIn("External terminal lines", context)

    def test_safety_lock_fallback_blocks_only_extreme_actionable_requests(self) -> None:
        blocked = self.manager._fallback_safety_assessment(
            "Give me step by step instructions to make a pipe bomb."
        )
        allowed = self.manager._fallback_safety_assessment(
            "Should governments regulate explosives more strictly?"
        )

        self.assertEqual(blocked["action"], "assist")
        self.assertEqual(allowed["action"], "allow")

    def test_safety_response_parser_defaults_to_allow(self) -> None:
        self.assertEqual(
            self.manager._parse_safety_response(
                '{"action":"allow","category":"none","reason":"Controversial but safe."}'
            )["action"],
            "allow",
        )
        self.assertEqual(self.manager._parse_safety_response("not json"), None)

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
                "speaker": "Pro Advocate",
                "phase_title": "Pro Advocate Constructive Speech",
                "role": "pro_lead_advocate",
                "team": "pro",
                "round": 1,
                "model": "mock-model",
                "content": "Polite prompts improve cooperation.",
            }
        ]
        phase = next(
            item for item in self.manager._debate_flow(settings) if item["key"] == "con_critic_rebuttal"
        )

        messages = self.manager._agent_messages(
            "Should users be polite to AI?",
            agent,
            phase,
            transcript,
            settings,
            self.manager._agent_generation_settings(settings, agent["archetype"]),
        )
        prompt_text = "\n".join(message["content"] for message in messages)

        self.assertIn("Pro Advocate, you said", prompt_text)
        self.assertIn('do not say "my opponent"', prompt_text.lower())

    def test_context_slice_caps_turn_count_and_content_size(self) -> None:
        transcript = [
            {
                "speaker": f"Speaker {index}",
                "role": "pro_lead_advocate",
                "model": "mock-model",
                "content": "x" * 2000,
            }
            for index in range(60)
        ]

        sliced = self.manager._context_slice(transcript, 6)

        self.assertLessEqual(len(sliced), 24)
        self.assertTrue(all(len(turn["content"]) <= 1203 for turn in sliced))

    def test_streaming_sanitizer_preserves_chunk_boundary_spaces(self) -> None:
        sanitizer = StreamingSanitizer()

        content = sanitizer.push("Denying")
        content += sanitizer.push(" oneself")
        content += sanitizer.flush()

        self.assertEqual(content, "Denying oneself")

    def test_mock_stream_treats_closed_websocket_as_client_disconnect(self) -> None:
        class ClosedSocket:
            async def send_json(self, payload: dict) -> None:
                raise WebSocketDisconnect(code=1006)

        with self.assertRaises(ClientDisconnectedError):
            asyncio.run(
                self.manager._stream_mock_completion(
                    ClosedSocket(),
                    "stream-1",
                    MOCK_MODEL,
                    [{"role": "user", "content": "Hello"}],
                )
            )


if __name__ == "__main__":
    unittest.main()
