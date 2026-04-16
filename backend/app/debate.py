from __future__ import annotations

import asyncio
import json
import re
from textwrap import dedent
from typing import Any
from uuid import uuid4

from fastapi import WebSocket

from .analytics import analyze_debate, format_analytics_report
from .config import settings
from .database import Database, utc_now
from .model_registry import MOCK_MODEL, SupportedModel, get_available_model


try:
    from litellm import acompletion
except ImportError:  # pragma: no cover - handled at runtime for clearer setup errors.
    acompletion = None


TEAM_ROLE_DEFINITIONS = (
    {
        "archetype": "lead_advocate",
        "label": "Lead Advocate",
        "min_debaters": 1,
        "job": "Build the team's central case, keep the argument coherent, and defend the main thesis.",
        "default_intent": "build the main case",
    },
    {
        "archetype": "rebuttal_critic",
        "label": "Rebuttal Critic",
        "min_debaters": 2,
        "job": "Attack the opposing team's strongest point and protect your team from direct criticism.",
        "default_intent": "rebut an opposing point",
    },
    {
        "archetype": "evidence_researcher",
        "label": "Evidence Researcher",
        "min_debaters": 3,
        "job": "Add evidence, examples, missing context, and careful uncertainty notes for your team.",
        "default_intent": "add evidence",
    },
    {
        "archetype": "cross_examiner",
        "label": "Cross-Examiner",
        "min_debaters": 4,
        "job": "Ask pressure questions, expose contradictions, and force the other team to answer clearly.",
        "default_intent": "cross-examine",
    },
)
TEAM_DEFINITIONS = (
    {
        "team": "pro",
        "team_label": "Pro",
        "stance_label": "supporting side",
        "stance": "argue for the topic or proposal",
    },
    {
        "team": "con",
        "team_label": "Con",
        "stance_label": "opposing side",
        "stance": "argue against the topic or proposal",
    },
)
JUDGE_ASSISTANT_DEFINITION = {
    "role": "judge_assistant",
    "archetype": "judge_assistant",
    "speaker": "Judge Assistant",
    "team": "neutral",
    "team_label": "Neutral",
    "stance_label": "neutral audit",
    "job": "Audit the debate for missed points, unanswered claims, evidence gaps, statistics, and scoring risks. Do not choose the final winner.",
}
JUDGE_DEFINITION = {
    "role": "judge",
    "archetype": "judge",
    "speaker": "Judge",
    "team": "neutral",
    "team_label": "Neutral",
    "stance_label": "final judgment",
    "job": "Use the debate and the Judge Assistant audit to make the final decision.",
}


class DebateError(Exception):
    pass


class CompletionStreamError(Exception):
    def __init__(self, original: Exception, had_output: bool):
        super().__init__(str(original))
        self.original = original
        self.had_output = had_output


class DebateManager:
    def __init__(self, db: Database):
        self.db = db
        self._active_debates: set[str] = set()
        self._active_sessions: set[str] = set()
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        return len(self._active_debates)

    async def run_interaction(
        self, websocket: WebSocket, session_id: str, content: str, selected_model_name: str
    ) -> None:
        cleaned_content = " ".join(content.strip().split())
        if not cleaned_content:
            raise DebateError("Please enter a message.")

        async with self._lock:
            if session_id in self._active_sessions:
                raise DebateError("This chat is already working. Other chats are still available.")
            self._active_sessions.add(session_id)

        try:
            session_settings = self._settings_snapshot(session_id)
            effective_model_name = selected_model_name.strip() or str(
                session_settings.get("overall_model", "")
            ).strip()
            selected_model = self._resolve_selected_model(effective_model_name)
            if self._council_assistant_always_on(session_settings):
                intent = "chat"
            else:
                intent = await self._classify_intent(
                    cleaned_content, selected_model, session_settings
                )
            if intent == "debate":
                await self.run_debate(websocket, session_id, cleaned_content, effective_model_name)
            else:
                await self.run_chat(websocket, session_id, cleaned_content, selected_model)
        finally:
            async with self._lock:
                self._active_sessions.discard(session_id)

    async def run_debate(
        self, websocket: WebSocket, session_id: str, topic: str, selected_model_name: str
    ) -> None:
        cleaned_topic = " ".join(topic.strip().split())
        if not cleaned_topic:
            raise DebateError("Please enter a debate topic.")

        opening_settings = self._settings_snapshot(session_id)
        effective_model_name = selected_model_name.strip() or str(
            opening_settings.get("overall_model", "")
        ).strip()
        selected_model = self._resolve_selected_model(effective_model_name)
        debate_rounds = opening_settings["debate_rounds"]

        async with self._lock:
            if len(self._active_debates) >= settings.max_active_debates:
                raise DebateError(
                    "Only 3 debates can run at the same time. Try again when one finishes."
                )
            debate = self.db.create_debate(session_id, cleaned_topic)
            debate_id = debate["id"]
            self._active_debates.add(debate_id)

        user_message = self.db.add_message(
            session_id=session_id,
            debate_id=debate_id,
            role="user",
            speaker="You",
            model="user",
            content=cleaned_topic,
        )
        await websocket.send_json(
            {"type": "message_completed", "stream_id": user_message["id"], "message": user_message}
        )
        await websocket.send_json(
            {
                "type": "debate_started",
                "debate": debate,
                "topic": cleaned_topic,
                "selected_model": selected_model.public_dict(configured=True),
                "assignments": self._assignment_payload(opening_settings, selected_model),
                "judge": {
                    "speaker": "Judge",
                    "model": self._resolve_agent_model(opening_settings, "judge", selected_model).name,
                    "provider": self._resolve_agent_model(opening_settings, "judge", selected_model).provider_label,
                },
                "active_debates": self.active_count,
            }
        )

        transcript: list[dict[str, Any]] = []
        latest_analysis = analyze_debate(cleaned_topic, transcript)
        try:
            max_possible_turns = 8 * 6
            for turn_index in range(max_possible_turns):
                turn_settings = self._settings_snapshot(session_id)
                active_agents = self._active_debate_agents(turn_settings)
                if not active_agents:
                    raise DebateError("At least one debater per team is required.")
                current_max_turns = len(active_agents) * int(
                    turn_settings.get("debate_rounds", debate_rounds)
                )
                if len(transcript) >= current_max_turns:
                    break

                bid = await self._select_turn_bid(
                    topic=cleaned_topic,
                    agents=active_agents,
                    transcript=transcript,
                    turn_index=turn_index,
                    max_turns=current_max_turns,
                    model=selected_model,
                    session_settings=turn_settings,
                )
                if not bid:
                    break

                round_number = self._round_for_turn(len(transcript), len(active_agents))
                turn_model = self._resolve_agent_model(
                    turn_settings, bid["agent"]["archetype"], selected_model
                )
                generation_settings = self._agent_generation_settings(
                    turn_settings, bid["agent"]["archetype"]
                )
                content = await self._stream_agent_turn(
                    websocket=websocket,
                    session_id=session_id,
                    debate_id=debate_id,
                    topic=cleaned_topic,
                    agent=bid["agent"],
                    model=turn_model,
                    round_number=round_number,
                    transcript=transcript,
                    session_settings=turn_settings,
                    generation_settings=generation_settings,
                    bid=bid,
                )
                transcript.append(
                    {
                        "speaker": bid["agent"]["speaker"],
                        "role": bid["agent"]["role"],
                        "team": bid["agent"]["team"],
                        "archetype": bid["agent"]["archetype"],
                        "round": round_number,
                        "model": turn_model.name,
                        "intent": bid["intent"],
                        "target": bid["target"],
                        "content": content,
                    }
                )
                latest_analysis = analyze_debate(cleaned_topic, transcript)
                await websocket.send_json(
                    {
                        "type": "analysis_updated",
                        "round": latest_analysis["round"],
                        "analysis": latest_analysis,
                    }
                )

            judge_assistant_report = ""
            if self._judge_assistant_enabled(self._settings_snapshot(session_id)):
                assistant_settings = self._settings_snapshot(session_id)
                assistant_model = self._resolve_agent_model(
                    assistant_settings, "judge_assistant", selected_model
                )
                judge_assistant_report = await self._stream_judge_assistant_turn(
                    websocket=websocket,
                    session_id=session_id,
                    debate_id=debate_id,
                    topic=cleaned_topic,
                    model=assistant_model,
                    transcript=transcript,
                    analysis=latest_analysis,
                    session_settings=assistant_settings,
                    generation_settings=self._agent_generation_settings(
                        assistant_settings, "judge_assistant"
                    ),
                )

            judge_settings = self._settings_snapshot(session_id)
            judge_model = self._resolve_agent_model(judge_settings, "judge", selected_model)
            judge_summary = await self._stream_judge_turn(
                websocket=websocket,
                session_id=session_id,
                debate_id=debate_id,
                topic=cleaned_topic,
                model=judge_model,
                transcript=transcript,
                analysis=latest_analysis,
                session_settings=judge_settings,
                generation_settings=self._agent_generation_settings(judge_settings, "judge"),
                judge_assistant_report=judge_assistant_report,
            )
            self.db.complete_debate(debate_id, judge_summary)
            await websocket.send_json(
                {
                    "type": "debate_completed",
                    "debate_id": debate_id,
                    "judge_summary": judge_summary,
                    "active_debates": self.active_count - 1,
                }
            )
        except Exception as exc:
            self.db.fail_debate(debate_id, str(exc))
            raise
        finally:
            async with self._lock:
                self._active_debates.discard(debate_id)

    async def run_chat(
        self, websocket: WebSocket, session_id: str, content: str, selected_model: SupportedModel
    ) -> None:
        session_settings = self._settings_snapshot(session_id)
        chat_record = self.db.create_debate(session_id, content, mode="chat")
        debate_id = chat_record["id"]
        user_message = self.db.add_message(
            session_id=session_id,
            debate_id=debate_id,
            role="user",
            speaker="You",
            model="user",
            content=content,
        )
        await websocket.send_json(
            {
                "type": "interaction_started",
                "mode": "chat",
                "debate": chat_record,
                "selected_model": selected_model.public_dict(configured=True),
            }
        )
        await websocket.send_json(
            {"type": "message_completed", "stream_id": user_message["id"], "message": user_message}
        )

        chat_model = self._resolve_agent_model(session_settings, "council_assistant", selected_model)
        chat_generation_settings = self._agent_generation_settings(
            session_settings, "council_assistant"
        )
        stream_id = str(uuid4())
        await websocket.send_json(
            {
                "type": "message_started",
                "stream_id": stream_id,
                "message": {
                    "id": stream_id,
                    "session_id": session_id,
                    "debate_id": debate_id,
                    "role": "assistant",
                    "speaker": "Council Assistant",
                    "model": chat_model.name,
                    "content": "",
                    "sequence": 0,
                    "created_at": utc_now(),
                },
                "round": "chat",
            }
        )
        messages = self._chat_messages(session_id, content, session_settings, chat_generation_settings)
        response = await self._stream_completion(
            websocket,
            stream_id,
            chat_model,
            messages,
            session_settings=chat_generation_settings,
        )
        saved = self.db.add_message(
            session_id=session_id,
            debate_id=debate_id,
            role="assistant",
            speaker="Council Assistant",
            model=chat_model.name,
            content=response,
        )
        self.db.complete_debate(debate_id, response)
        await websocket.send_json(
            {"type": "message_completed", "stream_id": stream_id, "message": saved}
        )
        await websocket.send_json(
            {"type": "interaction_completed", "mode": "chat", "debate_id": debate_id}
        )

    def _resolve_selected_model(self, selected_model_name: str) -> SupportedModel:
        cleaned_model_name = selected_model_name.strip()
        if settings.mock_llm and cleaned_model_name == MOCK_MODEL.name:
            return MOCK_MODEL
        if not cleaned_model_name:
            raise DebateError("Choose one unlocked model before starting the debate.")

        model = get_available_model(cleaned_model_name)
        if not model:
            raise DebateError(
                f"{cleaned_model_name} is not available. Add that provider API key to .env first."
            )
        return model

    def _resolve_role_model(
        self, session_settings: dict[str, Any], role: str, default_model: SupportedModel
    ) -> SupportedModel:
        role_model_name = (session_settings.get("role_models") or {}).get(role, "").strip()
        model_name = role_model_name or str(session_settings.get("overall_model", "")).strip()
        if not model_name:
            return default_model
        if settings.mock_llm and model_name == MOCK_MODEL.name:
            return MOCK_MODEL
        return get_available_model(model_name) or default_model

    def _settings_snapshot(self, session_id: str) -> dict[str, Any]:
        return self.db.get_session_settings(session_id) or {}

    def _active_debate_agents(self, session_settings: dict[str, Any]) -> list[dict[str, Any]]:
        debaters_per_team = max(1, min(4, int(session_settings.get("debaters_per_team", 3))))
        active_role_defs = [
            role_definition
            for role_definition in TEAM_ROLE_DEFINITIONS
            if role_definition["min_debaters"] <= debaters_per_team
        ]
        agents: list[dict[str, Any]] = []
        for team in TEAM_DEFINITIONS:
            for role_definition in active_role_defs:
                agents.append(
                    {
                        "role": f"{team['team']}_{role_definition['archetype']}",
                        "archetype": role_definition["archetype"],
                        "speaker": f"{team['team_label']} {role_definition['label']}",
                        "team": team["team"],
                        "team_label": team["team_label"],
                        "stance_label": team["stance_label"],
                        "stance": team["stance"],
                        "job": role_definition["job"],
                        "default_intent": role_definition["default_intent"],
                    }
                )
        return agents

    def _assignment_payload(
        self, session_settings: dict[str, Any], default_model: SupportedModel
    ) -> list[dict[str, str]]:
        agents = self._active_debate_agents(session_settings)
        if self._judge_assistant_enabled(session_settings):
            agents.append(JUDGE_ASSISTANT_DEFINITION)
        agents.append(JUDGE_DEFINITION)
        payload = []
        for agent in agents:
            model = self._resolve_agent_model(session_settings, agent["archetype"], default_model)
            payload.append(
                {
                    "role": agent["role"],
                    "speaker": agent["speaker"],
                    "model": model.name,
                    "provider": model.provider_label,
                }
            )
        return payload

    def _judge_assistant_enabled(self, session_settings: dict[str, Any]) -> bool:
        return bool(session_settings.get("judge_assistant_enabled", True))

    def _resolve_agent_model(
        self, session_settings: dict[str, Any], archetype: str, default_model: SupportedModel
    ) -> SupportedModel:
        raw_agent_settings = session_settings.get("agent_settings") or {}
        agent_settings = raw_agent_settings.get(archetype, {}) if isinstance(raw_agent_settings, dict) else {}
        model_name = str(agent_settings.get("model", "")).strip()
        if not model_name:
            model_name = str(session_settings.get("overall_model", "")).strip()
        if not model_name:
            return default_model
        if settings.mock_llm and model_name == MOCK_MODEL.name:
            return MOCK_MODEL
        return get_available_model(model_name) or default_model

    def _agent_generation_settings(
        self, session_settings: dict[str, Any], archetype: str
    ) -> dict[str, Any]:
        raw_agent_settings = session_settings.get("agent_settings") or {}
        agent_settings = raw_agent_settings.get(archetype, {}) if isinstance(raw_agent_settings, dict) else {}
        return {
            **session_settings,
            "temperature": float(agent_settings.get("temperature", session_settings.get("temperature", 0.55))),
            "max_tokens": int(agent_settings.get("max_tokens", session_settings.get("max_tokens", 700))),
            "response_length": str(agent_settings.get("response_length", session_settings.get("response_length", "Normal"))),
            "agent_web_search": bool(agent_settings.get("web_search", False)),
        }

    def _council_assistant_always_on(self, session_settings: dict[str, Any]) -> bool:
        raw_agent_settings = session_settings.get("agent_settings") or {}
        council_settings = (
            raw_agent_settings.get("council_assistant", {})
            if isinstance(raw_agent_settings, dict)
            else {}
        )
        return bool(council_settings.get("always_on", False))

    def _round_for_turn(self, completed_turns: int, active_debater_count: int) -> int:
        return (completed_turns // max(1, active_debater_count)) + 1

    async def _select_turn_bid(
        self,
        *,
        topic: str,
        agents: list[dict[str, Any]],
        transcript: list[dict[str, Any]],
        turn_index: int,
        max_turns: int,
        model: SupportedModel,
        session_settings: dict[str, Any],
    ) -> dict[str, Any] | None:
        if turn_index >= max_turns:
            return None
        latest = transcript[-1] if transcript else None

        if not latest:
            opener = next(agent for agent in agents if agent["team"] == "pro" and agent["archetype"] == "lead_advocate")
            return self._bid(opener, 0.98, "open the affirmative case", "the original topic", "A debate needs a clear Pro opening.")

        if len(transcript) == 1:
            opener = next(agent for agent in agents if agent["team"] == "con" and agent["archetype"] == "lead_advocate")
            return self._bid(opener, 0.98, "open the opposing case", latest["content"], "The Con team needs a direct opening response.")

        moderator_bid = await self._moderator_select_turn_bid(
            topic=topic,
            agents=agents,
            transcript=transcript,
            model=model,
            session_settings=session_settings,
        )
        if moderator_bid == "END":
            return None
        if isinstance(moderator_bid, dict):
            return moderator_bid

        return self._local_select_turn_bid(agents=agents, transcript=transcript)

    async def _moderator_select_turn_bid(
        self,
        *,
        topic: str,
        agents: list[dict[str, Any]],
        transcript: list[dict[str, Any]],
        model: SupportedModel,
        session_settings: dict[str, Any],
    ) -> dict[str, Any] | str | None:
        if settings.mock_llm or acompletion is None or not model.api_key:
            return None

        agent_lookup = {agent["role"]: agent for agent in agents}
        normalized_lookup = {
            self._normalize_role_token(agent["speaker"]): agent
            for agent in agents
        }
        normalized_lookup.update(
            {self._normalize_role_token(agent["role"]): agent for agent in agents}
        )
        candidate_lines = "\n".join(
            f"- {agent['role']}: {agent['speaker']} | {agent['team_label']} | {agent['job']}"
            for agent in agents
        )
        recent_transcript = self._format_transcript(
            self._context_slice(transcript, int(session_settings.get("context_window", 2)) + 1)
        )
        prompt = dedent(
            f"""
            Topic: {topic}

            Recent debate transcript:
            {recent_transcript}

            Valid speakers:
            {candidate_lines}

            Choose the next speaker like a human debate moderator. Do not follow a fixed role loop.
            Prefer the person who has a useful disagreement, answer, clarification, evidence addition, or pressure question.
            Return END only if another debater turn would be repetitive or the debate is ready for judging.

            Return strict JSON only:
            {{"role":"one valid role id or END","urgency":0.0-1.0,"intent":"short intent","target":"point being answered","reason":"why this speaker requested the floor"}}
            """
        ).strip()
        try:
            response = await acompletion(
                model=model.litellm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a neutral debate moderator. Select the next floor request. "
                            "You are not a debater and you do not write the debate turn."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                api_key=model.api_key,
                stream=False,
                temperature=0.0,
                max_tokens=180,
                timeout=min(settings.request_timeout_seconds, 30),
            )
            text = self._completion_text(response)
            payload = self._parse_json_object(text)
            if not payload:
                return None
            role = str(payload.get("role", "")).strip()
            if role.upper() == "END":
                return "END"
            agent = agent_lookup.get(role) or normalized_lookup.get(self._normalize_role_token(role))
            if not agent:
                return None
            urgency = self._clip_float(float(payload.get("urgency", 0.5)), 0.0, 1.0)
            intent = str(payload.get("intent") or agent["default_intent"])
            target = str(payload.get("target") or transcript[-1].get("content", "the latest point"))
            reason = str(payload.get("reason") or "the moderator selected this floor request")
            return self._bid(agent, urgency, intent, target, reason)
        except Exception:
            return None

    def _local_select_turn_bid(
        self,
        *,
        agents: list[dict[str, Any]],
        transcript: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        spoken_by_role = {turn.get("role") for turn in transcript}
        latest = transcript[-1] if transcript else None
        bids = []
        for agent in agents:
            if latest and agent["role"] == latest.get("role"):
                continue
            bid = self._score_agent_bid(agent, latest, transcript, spoken_by_role)
            if bid["urgency"] > 0.12:
                bids.append(bid)

        if not bids:
            return None
        return max(bids, key=lambda bid: bid["urgency"])

    def _score_agent_bid(
        self,
        agent: dict[str, Any],
        latest: dict[str, Any] | None,
        transcript: list[dict[str, Any]],
        spoken_by_role: set[str],
    ) -> dict[str, Any]:
        urgency = 0.2
        reasons = []
        intent = agent["default_intent"]
        target = latest["content"] if latest else "the original topic"
        latest_team = latest.get("team") if latest else None

        if agent["role"] not in spoken_by_role:
            urgency += 0.12
            reasons.append("this role has not spoken yet")
        if latest_team and latest_team != agent["team"]:
            urgency += 0.24
            reasons.append("the other team just made a point")
        if latest and "?" in str(latest.get("content", "")) and latest_team != agent["team"]:
            urgency += 0.18
            intent = "answer a pressure question"
            reasons.append("there is a direct question to answer")

        archetype = agent["archetype"]
        latest_text = str(latest.get("content", "") if latest else "").lower()
        if archetype == "rebuttal_critic" and latest_team != agent["team"]:
            urgency += 0.22
            intent = "rebut the latest opposing claim"
        elif archetype == "evidence_researcher":
            if any(word in latest_text for word in ("evidence", "data", "study", "because", "example")):
                urgency += 0.18
                intent = "test and add evidence"
            elif agent["role"] not in spoken_by_role:
                urgency += 0.12
        elif archetype == "cross_examiner":
            recent_questions = sum(1 for turn in transcript[-4:] if "?" in str(turn.get("content", "")))
            if recent_questions < 2:
                urgency += 0.16
                intent = "ask a pressure question"
        elif archetype == "lead_advocate" and latest_team != agent["team"]:
            urgency += 0.1
            intent = "defend the team's main thesis"

        recent_roles = [turn.get("role") for turn in transcript[-3:]]
        if agent["role"] in recent_roles:
            urgency -= 0.22
        recent_teams = [turn.get("team") for turn in transcript[-2:]]
        if len(recent_teams) == 2 and recent_teams[0] == recent_teams[1] == agent["team"]:
            urgency -= 0.28

        reason = "; ".join(reasons) or "this contribution best fits the open tension"
        return self._bid(agent, max(0.0, min(1.0, urgency)), intent, target, reason)

    def _bid(
        self,
        agent: dict[str, Any],
        urgency: float,
        intent: str,
        target: str,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "agent": agent,
            "urgency": round(urgency, 3),
            "intent": intent,
            "target": self._clip_for_prompt(target, 360),
            "reason": reason,
        }

    def _clip_for_prompt(self, text: str, limit: int) -> str:
        normalized = " ".join(str(text).strip().split())
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 3].rstrip() + "..."

    def _parse_json_object(self, text: str) -> dict[str, Any] | None:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def _normalize_role_token(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    def _clip_float(self, value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))

    async def _stream_agent_turn(
        self,
        *,
        websocket: WebSocket,
        session_id: str,
        debate_id: str,
        topic: str,
        agent: dict[str, Any],
        model: SupportedModel,
        round_number: int,
        transcript: list[dict[str, Any]],
        session_settings: dict[str, Any],
        generation_settings: dict[str, Any],
        bid: dict[str, Any],
    ) -> str:
        stream_id = str(uuid4())
        await websocket.send_json(
            {
                "type": "message_started",
                "stream_id": stream_id,
                "message": {
                    "id": stream_id,
                    "session_id": session_id,
                    "debate_id": debate_id,
                    "role": agent["role"],
                    "speaker": agent["speaker"],
                    "model": model.name,
                    "content": "",
                    "sequence": 0,
                    "created_at": utc_now(),
                },
                "round": round_number,
            }
        )

        messages = self._agent_messages(
            topic, agent, round_number, transcript, session_settings, generation_settings, bid
        )
        content = await self._stream_completion(
            websocket,
            stream_id,
            model,
            messages,
            session_settings=generation_settings,
        )
        saved = self.db.add_message(
            session_id=session_id,
            debate_id=debate_id,
            role=agent["role"],
            speaker=agent["speaker"],
            model=model.name,
            content=content,
        )
        await websocket.send_json(
            {"type": "message_completed", "stream_id": stream_id, "message": saved}
        )
        return content

    async def _stream_debater_turn(
        self,
        *,
        websocket: WebSocket,
        session_id: str,
        debate_id: str,
        topic: str,
        role_definition: dict[str, str],
        model: SupportedModel,
        round_number: int,
        transcript: list[dict[str, Any]],
        session_settings: dict[str, Any],
    ) -> str:
        stream_id = str(uuid4())
        speaker = role_definition["speaker"]
        role = role_definition["role"]
        await websocket.send_json(
            {
                "type": "message_started",
                "stream_id": stream_id,
                "message": {
                    "id": stream_id,
                    "session_id": session_id,
                    "debate_id": debate_id,
                    "role": role,
                    "speaker": speaker,
                    "model": model.name,
                    "content": "",
                    "sequence": 0,
                    "created_at": utc_now(),
                },
                "round": round_number,
            }
        )

        messages = self._debater_messages(
            topic, role_definition, round_number, transcript, session_settings
        )
        content = await self._stream_completion(
            websocket,
            stream_id,
            model,
            messages,
            session_settings=session_settings,
        )
        saved = self.db.add_message(
            session_id=session_id,
            debate_id=debate_id,
            role=role,
            speaker=speaker,
            model=model.name,
            content=content,
        )
        await websocket.send_json(
            {"type": "message_completed", "stream_id": stream_id, "message": saved}
        )
        return content

    async def _stream_judge_turn(
        self,
        *,
        websocket: WebSocket,
        session_id: str,
        debate_id: str,
        topic: str,
        model: SupportedModel,
        transcript: list[dict[str, Any]],
        analysis: dict[str, Any],
        session_settings: dict[str, Any],
        generation_settings: dict[str, Any],
        judge_assistant_report: str,
    ) -> str:
        stream_id = str(uuid4())
        await websocket.send_json(
            {
                "type": "message_started",
                "stream_id": stream_id,
                "message": {
                    "id": stream_id,
                    "session_id": session_id,
                    "debate_id": debate_id,
                    "role": "judge",
                    "speaker": "Judge",
                    "model": model.name,
                    "content": "",
                    "sequence": 0,
                    "created_at": utc_now(),
                },
                "round": "summary",
            }
        )
        messages = self._judge_messages(
            topic, transcript, analysis, session_settings, generation_settings, judge_assistant_report
        )
        content = await self._stream_completion(
            websocket,
            stream_id,
            model,
            messages,
            session_settings=generation_settings,
        )
        saved = self.db.add_message(
            session_id=session_id,
            debate_id=debate_id,
            role="judge",
            speaker="Judge",
            model=model.name,
            content=content,
        )
        await websocket.send_json(
            {"type": "message_completed", "stream_id": stream_id, "message": saved}
        )
        return content

    async def _stream_judge_assistant_turn(
        self,
        *,
        websocket: WebSocket,
        session_id: str,
        debate_id: str,
        topic: str,
        model: SupportedModel,
        transcript: list[dict[str, Any]],
        analysis: dict[str, Any],
        session_settings: dict[str, Any],
        generation_settings: dict[str, Any],
    ) -> str:
        stream_id = str(uuid4())
        await websocket.send_json(
            {
                "type": "message_started",
                "stream_id": stream_id,
                "message": {
                    "id": stream_id,
                    "session_id": session_id,
                    "debate_id": debate_id,
                    "role": "judge_assistant",
                    "speaker": "Judge Assistant",
                    "model": model.name,
                    "content": "",
                    "sequence": 0,
                    "created_at": utc_now(),
                },
                "round": "summary",
            }
        )
        messages = self._judge_assistant_messages(
            topic, transcript, analysis, session_settings, generation_settings
        )
        content = await self._stream_completion(
            websocket,
            stream_id,
            model,
            messages,
            session_settings=generation_settings,
        )
        saved = self.db.add_message(
            session_id=session_id,
            debate_id=debate_id,
            role="judge_assistant",
            speaker="Judge Assistant",
            model=model.name,
            content=content,
        )
        await websocket.send_json(
            {"type": "message_completed", "stream_id": stream_id, "message": saved}
        )
        return content

    async def _stream_completion(
        self,
        websocket: WebSocket,
        stream_id: str,
        model: SupportedModel,
        messages: list[dict[str, str]],
        session_settings: dict[str, Any] | None = None,
    ) -> str:
        if settings.mock_llm:
            return await self._stream_mock_completion(websocket, stream_id, model, messages)

        if acompletion is None:
            raise DebateError("LiteLLM is not installed. Run pip install -r backend/requirements.txt.")
        if not model.api_key:
            raise DebateError(f"{model.api_key_env} is missing for {model.name}.")

        generation_settings = session_settings or {}
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                content, finish_reason = await self._stream_completion_once(
                    websocket,
                    stream_id,
                    model,
                    messages,
                    generation_settings,
                )
                if finish_reason in {"length", "max_tokens"}:
                    content = await self._continue_truncated_completion(
                        websocket,
                        stream_id,
                        model,
                        messages,
                        content,
                        generation_settings,
                    )
                return content
            except CompletionStreamError as exc:
                if (
                    self._is_retryable_provider_error(exc.original)
                    and not exc.had_output
                    and attempt < max_attempts - 1
                ):
                    await asyncio.sleep(1.2 * (attempt + 1))
                    continue
                raise DebateError(
                    f"{model.name} failed through LiteLLM: {exc.original}"
                ) from exc.original

        raise DebateError(f"{model.name} failed through LiteLLM after retries.")

    async def _stream_completion_once(
        self,
        websocket: WebSocket,
        stream_id: str,
        model: SupportedModel,
        messages: list[dict[str, str]],
        generation_settings: dict[str, Any],
    ) -> tuple[str, str | None]:
        parts: list[str] = []
        finish_reason: str | None = None
        sanitizer = StreamingSanitizer()
        try:
            response = await acompletion(
                model=model.litellm_model,
                messages=messages,
                api_key=model.api_key,
                stream=True,
                temperature=float(generation_settings.get("temperature", 0.55)),
                max_tokens=int(generation_settings.get("max_tokens", 700)),
                timeout=settings.request_timeout_seconds,
            )
            async for chunk in response:
                finish_reason = self._extract_finish_reason(chunk) or finish_reason
                delta = self._extract_delta(chunk)
                if not delta:
                    continue
                visible_delta = sanitizer.push(delta)
                if not visible_delta:
                    continue
                parts.append(visible_delta)
                await websocket.send_json(
                    {"type": "message_delta", "stream_id": stream_id, "delta": visible_delta}
                )
            tail = sanitizer.flush()
            if tail:
                parts.append(tail)
                await websocket.send_json(
                    {"type": "message_delta", "stream_id": stream_id, "delta": tail}
                )
        except Exception as exc:
            raise CompletionStreamError(exc, had_output=bool(parts)) from exc

        content = sanitize_model_text("".join(parts)).strip()
        if not content:
            raise DebateError(f"{model.name} returned an empty response.")
        return content, finish_reason

    async def _continue_truncated_completion(
        self,
        websocket: WebSocket,
        stream_id: str,
        model: SupportedModel,
        messages: list[dict[str, str]],
        existing_content: str,
        generation_settings: dict[str, Any],
    ) -> str:
        continuation_settings = {
            **generation_settings,
            "max_tokens": min(900, max(320, int(generation_settings.get("max_tokens", 700)))),
        }
        continuation_messages = [
            *messages,
            {"role": "assistant", "content": existing_content[-4000:]},
            {
                "role": "user",
                "content": (
                    "Continue exactly where the previous answer stopped. Do not repeat earlier text. "
                    "Finish the remaining required sections briefly and end cleanly."
                ),
            },
        ]
        separator = "" if existing_content.endswith((" ", "\n", "-", "/", "(")) else "\n"
        if separator:
            await websocket.send_json(
                {"type": "message_delta", "stream_id": stream_id, "delta": separator}
            )
        try:
            continuation, finish_reason = await self._stream_completion_once(
                websocket,
                stream_id,
                model,
                continuation_messages,
                continuation_settings,
            )
        except CompletionStreamError as exc:
            notice = (
                "\n\n_Response stopped early because the provider interrupted the continuation. "
                "Try increasing this role's Max tokens or retrying the message._"
            )
            await websocket.send_json(
                {"type": "message_delta", "stream_id": stream_id, "delta": notice}
            )
            return f"{existing_content}{separator}{notice}"

        combined = f"{existing_content}{separator}{continuation}".strip()
        if finish_reason in {"length", "max_tokens"}:
            notice = (
                "\n\n_Response reached the max-token limit. Increase this role's Max tokens "
                "in Chat Settings for a fuller answer._"
            )
            await websocket.send_json(
                {"type": "message_delta", "stream_id": stream_id, "delta": notice}
            )
            combined = f"{combined}{notice}"
        return combined

    def _is_retryable_provider_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return any(
            marker in text
            for marker in (
                "529",
                "overloaded",
                "high load",
                "temporarily unavailable",
                "timeout",
                "api connection",
                "connectionerror",
                "rate limit",
            )
        )

    async def _stream_mock_completion(
        self,
        websocket: WebSocket,
        stream_id: str,
        model: SupportedModel,
        messages: list[dict[str, str]],
    ) -> str:
        prompt = messages[-1]["content"]
        content = sanitize_model_text(
            f"{model.name}: {prompt[:220]} "
            "The central tradeoff is clear, but the strongest answer depends on evidence, incentives, and failure modes."
        )
        for word in content.split(" "):
            delta = word + " "
            await asyncio.sleep(0.04)
            await websocket.send_json(
                {"type": "message_delta", "stream_id": stream_id, "delta": delta}
            )
        return content.strip()

    def _agent_messages(
        self,
        topic: str,
        agent: dict[str, Any],
        round_number: int,
        transcript: list[dict[str, Any]],
        session_settings: dict[str, Any],
        generation_settings: dict[str, Any],
        bid: dict[str, Any],
    ) -> list[dict[str, str]]:
        latest_speaker = transcript[-1]["speaker"] if transcript else "the previous speaker"
        previous_debate = self._format_transcript(
            self._context_slice(transcript, int(session_settings.get("context_window", 2)))
        )
        response_length = generation_settings.get("response_length", "Normal")
        word_limit = {"Concise": 120, "Normal": 180, "Detailed": 260}.get(response_length, 180)
        advanced_notes = []
        if agent["archetype"] == "evidence_researcher" and generation_settings.get("agent_web_search"):
            advanced_notes.append(
                "Web-search mode is enabled for this researcher; when no live source is available, mark claims needing verification instead of inventing citations."
            )
        if session_settings.get("fact_check_mode"):
            advanced_notes.append(
                "Fact-check mode is enabled; flag uncertain factual claims and separate evidence from interpretation."
            )
        advanced_prompt = "\n".join(advanced_notes) or "No extra advanced constraints."
        user_prompt = dedent(
            f"""
            Topic: {topic}

            Debate so far:
            {previous_debate}

            You requested the floor because: {bid["reason"]}
            Current intent: {bid["intent"]}.
            Target to address: {bid["target"]}.
            Latest speaker to answer: {latest_speaker}.

            Speak naturally as {agent["speaker"]}. Address another debater directly when useful, like a human debate.
            Prefer direct phrasing such as "{latest_speaker}, you said..." or "I disagree with your point about...".
            Do not narrate the debate with phrases like "my opponent says", "my opponent argues", "the opponent says", or "the opposing side says".
            Do your role's job, stay on the {agent["stance_label"]}, and keep this turn under {word_limit} words.
            If you disagree, say exactly what you disagree with and why. If you add evidence, explain how it changes the debate.
            """
        ).strip()
        return [
            {
                "role": "system",
                "content": dedent(
                    f"""
                    You are {agent["speaker"]} in an AI debate council.
                    Team: {agent["team_label"]} ({agent["stance"]}).
                    Your job: {agent["job"]}
                    Debate tone: {session_settings.get("debate_tone", "Academic")}.
                    Language: {session_settings.get("language", "English")}.
                    You are already this debater. Never say the user wants you to act as this role.
                    Never expose hidden reasoning, chain-of-thought, planning notes, or <think> blocks.
                    Advanced constraints: {advanced_prompt}
                    Use polished Markdown when useful.
                    Be responsive to the actual prior speaker, not generic. Stay in role and do not judge the debate.
                    You are in the room with the other debaters. Use their speaker names or second-person address; do not say "my opponent" or "the opponent".
                    """
                ).strip(),
            },
            {"role": "user", "content": user_prompt},
        ]

    def _judge_assistant_messages(
        self,
        topic: str,
        transcript: list[dict[str, Any]],
        analysis: dict[str, Any],
        session_settings: dict[str, Any],
        generation_settings: dict[str, Any],
    ) -> list[dict[str, str]]:
        response_length = generation_settings.get("response_length", "Normal")
        word_limit = {"Concise": 220, "Normal": 340, "Detailed": 520}.get(response_length, 340)
        return [
            {
                "role": "system",
                "content": dedent(
                    f"""
                    You are the Judge Assistant. You are neutral and you do not choose the final winner.
                    Your job is to help the Judge by finding missed points, unanswered claims, evidence gaps, contradictions, and useful statistics.
                    Never expose hidden reasoning, planning notes, or <think> blocks.
                    Tone: {session_settings.get("debate_tone", "Academic")}.
                    Language: {session_settings.get("language", "English")}.
                    """
                ).strip(),
            },
            {
                "role": "user",
                "content": dedent(
                    f"""
                    Topic: {topic}

                    Transcript:
                    {self._format_transcript(transcript)}

                    Debate analytics:
                    {format_analytics_report(analysis)}

                    Produce a Judge Assistant audit under {word_limit} words:
                    - Strongest Pro points
                    - Strongest Con points
                    - Unanswered or underanswered points
                    - Evidence quality warnings
                    - Statistics the Judge should consider
                    - What the Judge must not overlook

                    Do not name a final winner.
                    """
                ).strip(),
            },
        ]

    def _debater_messages(
        self,
        topic: str,
        role_definition: dict[str, str],
        round_number: int,
        transcript: list[dict[str, Any]],
        session_settings: dict[str, Any],
    ) -> list[dict[str, str]]:
        latest_speaker = transcript[-1]["speaker"] if transcript else "the previous speaker"
        previous_debate = self._format_transcript(
            self._context_slice(transcript, int(session_settings.get("context_window", 2)))
        )
        response_length = session_settings.get("response_length", "Normal")
        word_limit = {"Concise": 120, "Normal": 180, "Detailed": 260}.get(response_length, 180)
        advanced_notes = []
        if role_definition["role"] == "researcher" and session_settings.get("researcher_web_search"):
            advanced_notes.append(
                "Researcher web-search mode is enabled; when no live source is available, mark claims that need outside verification instead of inventing citations."
            )
        if session_settings.get("fact_check_mode"):
            advanced_notes.append(
                "Fact-check mode is enabled; flag uncertain factual claims and separate evidence from interpretation."
            )
        advanced_prompt = "\n".join(advanced_notes) or "No extra advanced constraints."
        if round_number == 1:
            user_prompt = dedent(
                f"""
                Topic: {topic}

                Give your opening argument as {role_definition["speaker"]}.
                Keep it under {word_limit} words, use concrete reasoning, and end with one pressure-test question for the council.
                """
            ).strip()
        else:
            user_prompt = dedent(
                f"""
                Topic: {topic}

                Debate so far:
                {previous_debate}

                Respond as {role_definition["speaker"]}. Strengthen your position, address at least one opposing point,
                answer {latest_speaker} directly when useful, and avoid phrases like "my opponent says" or "the opponent argues".
                and keep the turn under {word_limit} words.
                """
            ).strip()

        return [
            {
                "role": "system",
                "content": dedent(
                    f"""
                    You are {role_definition["speaker"]} in an AI debate council.
                    Your job: {role_definition["stance"]}
                    Debate tone: {session_settings.get("debate_tone", "Academic")}.
                    Language: {session_settings.get("language", "English")}.
                    You are already this council role. Never say the user wants you to act as this role.
                    Never expose hidden reasoning, chain-of-thought, planning notes, or <think> blocks.
                    Advanced constraints: {advanced_prompt}
                    Use polished Markdown for headings, lists, and emphasis when useful.
                    Be rigorous, concrete, and avoid generic filler.
                    Use direct in-room debate language. Say "you said..." or use speaker names instead of "my opponent" or "the opponent".
                    """
                ).strip(),
            },
            {"role": "user", "content": user_prompt},
        ]

    def _judge_messages(
        self,
        topic: str,
        transcript: list[dict[str, Any]],
        analysis: dict[str, Any],
        session_settings: dict[str, Any],
        generation_settings: dict[str, Any],
        judge_assistant_report: str,
    ) -> list[dict[str, str]]:
        assistant_section = judge_assistant_report or "Judge Assistant disabled for this debate."
        response_length = generation_settings.get("response_length", "Normal")
        configured_word_limit = {"Concise": 220, "Normal": 360, "Detailed": 560}.get(
            response_length, 360
        )
        token_word_limit = max(140, int(int(generation_settings.get("max_tokens", 700)) * 0.5))
        word_limit = min(configured_word_limit, token_word_limit)
        return [
            {
                "role": "system",
                "content": (
                    "You are the Judge AI. You are already the final arbiter of this debate. "
                    "Never mention that the user wants you to judge. Never expose hidden reasoning or <think> blocks. "
                    "Give a concrete, confident verdict. Pick a winner, state exactly why, and identify what would change your mind. "
                    "If space is tight, use shorter bullets instead of leaving the verdict unfinished."
                ),
            },
            {
                "role": "user",
                "content": dedent(
                    f"""
                    Topic: {topic}

                    Transcript:
                    {self._format_transcript(transcript)}

                    Judge Assistant audit:
                    {assistant_section}

                    Debate analytics:
                    {format_analytics_report(analysis)}

                    Produce a concise verdict with:
                    1. Best affirmative argument
                    2. Best skeptical argument
                    3. Best evidence or research need
                    4. Where the analytics agree or disagree with your own judgment
                    5. Clear winner: name the winning statement or stance
                    6. Why it wins, with concrete criteria

                    Tone: {session_settings.get("debate_tone", "Academic")}
                    Language: {session_settings.get("language", "English")}
                    Response length: {response_length}
                    Hard limit: under {word_limit} words. Finish all 6 sections.
                    """
                ).strip(),
            },
        ]

    def _chat_messages(
        self,
        session_id: str,
        user_message: str,
        session_settings: dict[str, Any],
        generation_settings: dict[str, Any],
    ) -> list[dict[str, str]]:
        history = self.db.list_messages(session_id, include_hidden=True)[-18:]
        formatted_history = "\n".join(
            f"{message['speaker']} ({message['role']}): {message['content']}"
            for message in history
            if message["content"] != user_message
        )
        return [
            {
                "role": "system",
                "content": dedent(
                    f"""
                    You are the AI Debate Council assistant for this chat.
                    Answer normal chat messages directly and use the chat memory below when relevant.
                    If the user asks about a past debate, explain the result from memory.
                    Do not start a new debate unless the user clearly asks for debate, comparison, pros/cons, or multiple sides.
                    Never expose hidden reasoning, planning notes, or <think> blocks.
                    Tone: {session_settings.get("debate_tone", "Academic")}.
                    Language: {session_settings.get("language", "English")}.
                    Response length: {generation_settings.get("response_length", "Normal")}.
                    """
                ).strip(),
            },
            {
                "role": "user",
                "content": dedent(
                    f"""
                    Chat memory:
                    {formatted_history or "No previous messages yet."}

                    Current user message:
                    {user_message}
                    """
                ).strip(),
            },
        ]

    async def _classify_intent(
        self, content: str, model: SupportedModel, session_settings: dict[str, Any]
    ) -> str:
        heuristic = self._heuristic_intent(content)
        if heuristic == "debate":
            return "debate"
        if heuristic == "chat":
            return "chat"
        if settings.mock_llm or acompletion is None:
            return "chat"
        try:
            response = await acompletion(
                model=model.litellm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Classify the user's message as exactly one word: debate or chat. "
                            "Use debate for requests asking multiple sides, pros and cons, comparisons, policy judgment, "
                            "or explicit debate. Use chat for greetings, follow-up questions, clarifications, and simple help."
                        ),
                    },
                    {"role": "user", "content": content},
                ],
                api_key=model.api_key,
                stream=False,
                temperature=0.0,
                max_tokens=3,
                timeout=min(settings.request_timeout_seconds, 30),
            )
            text = self._completion_text(response).strip().lower()
            return "debate" if "debate" in text else "chat"
        except Exception:
            fallback = self._heuristic_intent(content)
            return "chat" if fallback == "ambiguous" else fallback

    def _heuristic_intent(self, content: str) -> str:
        lower = content.lower().strip()
        direct_chat_markers = (
            "hello",
            "hi",
            "thanks",
            "thank you",
            "explain",
            "summarize",
            "what did",
            "what should i",
            "what command",
            "can you tell me",
            "how do i",
            "how do we",
            "setup",
            "run it",
            "start the program",
        )
        explicit_debate_markers = (
            "debate",
            "let them debate",
            "let it debate",
            "start a debate",
            "run a debate",
            "argue both sides",
            "pro and con",
            "for and against",
            "pros and cons",
        )
        debate_markers = (
            "argue",
            "whether",
            "should ",
            " vs ",
            "versus",
            "which is better",
        )
        if any(marker in lower for marker in explicit_debate_markers):
            return "debate"
        if any(marker in lower for marker in direct_chat_markers):
            return "chat"
        if any(marker in lower for marker in debate_markers):
            return "debate"
        return "ambiguous"

    def _context_slice(self, transcript: list[dict[str, Any]], context_window: int) -> list[dict[str, Any]]:
        if context_window <= 0:
            return []
        return transcript[-context_window * 8 :]

    def _format_transcript(self, transcript: list[dict[str, Any]]) -> str:
        if not transcript:
            return "No prior turns yet."
        return "\n\n".join(
            f"{turn['speaker']} ({turn['model']}): {turn['content']}" for turn in transcript
        )

    def _extract_delta(self, chunk: Any) -> str:
        if isinstance(chunk, dict):
            choices = chunk.get("choices") or []
            if not choices:
                return ""
            delta = choices[0].get("delta") or {}
            if isinstance(delta, dict):
                return delta.get("content") or ""
            return getattr(delta, "content", "") or ""

        choices = getattr(chunk, "choices", None) or []
        if not choices:
            return ""
        choice = choices[0]
        delta = getattr(choice, "delta", None)
        if isinstance(delta, dict):
            return delta.get("content") or ""
        return getattr(delta, "content", "") or ""

    def _extract_finish_reason(self, chunk: Any) -> str | None:
        if isinstance(chunk, dict):
            choices = chunk.get("choices") or []
            if not choices:
                return None
            reason = choices[0].get("finish_reason")
            return str(reason) if reason else None

        choices = getattr(chunk, "choices", None) or []
        if not choices:
            return None
        reason = getattr(choices[0], "finish_reason", None)
        return str(reason) if reason else None

    def _completion_text(self, response: Any) -> str:
        if isinstance(response, dict):
            choices = response.get("choices") or []
            if not choices:
                return ""
            message = choices[0].get("message") or {}
            if isinstance(message, dict):
                return message.get("content") or ""
            return getattr(message, "content", "") or ""
        choices = getattr(response, "choices", None) or []
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        if isinstance(message, dict):
            return message.get("content") or ""
        return getattr(message, "content", "") or ""


class StreamingSanitizer:
    def __init__(self) -> None:
        self.in_think = False
        self.pending = ""

    def push(self, delta: str) -> str:
        text = self.pending + delta
        self.pending = ""
        output: list[str] = []

        while text:
            lower = text.lower()
            if self.in_think:
                end_index = lower.find("</think>")
                if end_index == -1:
                    return ""
                text = text[end_index + len("</think>") :]
                self.in_think = False
                continue

            start_index = lower.find("<think>")
            if start_index == -1:
                keep = max(len("<think>") - 1, len("</think>") - 1)
                if len(text) > keep:
                    output.append(text[:-keep])
                    self.pending = text[-keep:]
                else:
                    self.pending = text
                break

            output.append(text[:start_index])
            text = text[start_index + len("<think>") :]
            self.in_think = True

        return sanitize_model_text("".join(output), remove_partial_meta=False)

    def flush(self) -> str:
        if self.in_think:
            self.pending = ""
            return ""
        tail = self.pending
        self.pending = ""
        return sanitize_model_text(tail, remove_partial_meta=False)


def sanitize_model_text(text: str, *, remove_partial_meta: bool = True) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"</?think>", "", cleaned, flags=re.IGNORECASE)
    if remove_partial_meta:
        cleaned = re.sub(
            r"(?im)^\s*(i see|i understand|the user wants|the user asks|let me|i need to|we need to).*?(?:\n|$)",
            "",
            cleaned,
        )
    return cleaned.strip()
