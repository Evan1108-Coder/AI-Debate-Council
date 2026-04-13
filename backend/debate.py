import asyncio
import json
import traceback
from typing import AsyncGenerator
from litellm import acompletion
from models import DebaterRole, MODEL_MAP

# Track active debates for concurrency limit
active_debates: set[int] = set()
MAX_CONCURRENT_DEBATES = 3

ROLE_SYSTEM_PROMPTS = {
    DebaterRole.ADVOCATE: (
        "You are the Advocate in a structured debate. Your role is to argue IN FAVOR of the topic. "
        "Present strong, well-reasoned arguments supporting the position. Use evidence, logic, and "
        "persuasive reasoning. Be passionate but factual. Keep responses concise (2-3 paragraphs max)."
    ),
    DebaterRole.CRITIC: (
        "You are the Critic in a structured debate. Your role is to argue AGAINST the topic. "
        "Identify weaknesses, flaws, and counterarguments. Challenge assumptions and point out risks. "
        "Be rigorous and analytical. Keep responses concise (2-3 paragraphs max)."
    ),
    DebaterRole.RESEARCHER: (
        "You are the Researcher in a structured debate. Your role is to provide FACTUAL CONTEXT "
        "and evidence from multiple perspectives. Present data, studies, historical examples, and "
        "expert opinions relevant to the topic. Stay neutral and informative. Keep responses concise (2-3 paragraphs max)."
    ),
    DebaterRole.DEVILS_ADVOCATE: (
        "You are the Devil's Advocate in a structured debate. Your role is to challenge ALL sides "
        "by presenting unexpected angles, edge cases, and contrarian viewpoints that others may have "
        "overlooked. Push the debate into unexplored territory. Keep responses concise (2-3 paragraphs max)."
    ),
    DebaterRole.JUDGE: (
        "You are the Judge in a structured debate. After reviewing all arguments from the Advocate, "
        "Critic, Researcher, and Devil's Advocate, provide a balanced verdict. Evaluate the strength "
        "of each argument, identify the most compelling points, acknowledge nuances, and deliver a "
        "final judgment. Be fair and thorough. Keep your verdict to 3-4 paragraphs."
    ),
}

DEBATER_ORDER = [
    DebaterRole.ADVOCATE,
    DebaterRole.CRITIC,
    DebaterRole.RESEARCHER,
    DebaterRole.DEVILS_ADVOCATE,
]


def can_start_debate() -> bool:
    return len(active_debates) < MAX_CONCURRENT_DEBATES


async def run_debate(
    session_id: int,
    topic: str,
    model: str,
    rounds: int,
    message_callback,
) -> AsyncGenerator[dict, None]:
    """Run a full debate with multiple rounds + judge verdict."""
    if not can_start_debate():
        yield {"type": "error", "message": "Maximum concurrent debates (3) reached. Please wait for a debate to finish."}
        return

    active_debates.add(session_id)
    litellm_model = MODEL_MAP.get(model, f"openai/{model}")
    conversation_history = []

    try:
        yield {"type": "status", "message": "Debate started", "topic": topic}

        for round_num in range(1, rounds + 1):
            yield {"type": "round", "round": round_num, "total_rounds": rounds}

            for role in DEBATER_ORDER:
                yield {"type": "debater_start", "role": role.value, "round": round_num}

                # Build messages for this debater
                messages = [
                    {"role": "system", "content": ROLE_SYSTEM_PROMPTS[role]},
                    {"role": "user", "content": f"Debate topic: {topic}"},
                ]

                if conversation_history:
                    history_text = "\n\n".join(
                        f"[{msg['role_name']}]: {msg['content']}"
                        for msg in conversation_history
                    )
                    messages.append({
                        "role": "user",
                        "content": f"Previous arguments in this debate:\n\n{history_text}\n\nNow provide your {'response for round ' + str(round_num) if round_num > 1 else 'opening argument'}.",
                    })

                full_response = ""
                try:
                    response = await acompletion(
                        model=litellm_model,
                        messages=messages,
                        stream=True,
                        temperature=0.8,
                        max_tokens=1024,
                    )

                    async for chunk in response:
                        if chunk.choices[0].delta.content:
                            token = chunk.choices[0].delta.content
                            full_response += token
                            yield {"type": "token", "role": role.value, "content": token}

                except Exception as e:
                    error_msg = f"Error from {role.value}: {str(e)}"
                    full_response = f"[Model error: {str(e)}]"
                    yield {"type": "error", "message": error_msg}

                conversation_history.append({
                    "role_name": role.value,
                    "content": full_response,
                })

                await message_callback(session_id, role.value, full_response)
                yield {"type": "debater_end", "role": role.value, "round": round_num}

        # Judge's verdict
        yield {"type": "debater_start", "role": "Judge", "round": 0}

        judge_messages = [
            {"role": "system", "content": ROLE_SYSTEM_PROMPTS[DebaterRole.JUDGE]},
            {"role": "user", "content": f"Debate topic: {topic}"},
            {
                "role": "user",
                "content": "Here is the full debate:\n\n"
                + "\n\n".join(
                    f"[{msg['role_name']}]: {msg['content']}"
                    for msg in conversation_history
                )
                + "\n\nPlease provide your final verdict.",
            },
        ]

        judge_response = ""
        try:
            response = await acompletion(
                model=litellm_model,
                messages=judge_messages,
                stream=True,
                temperature=0.6,
                max_tokens=1500,
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    judge_response += token
                    yield {"type": "token", "role": "Judge", "content": token}

        except Exception as e:
            judge_response = f"[Judge error: {str(e)}]"
            yield {"type": "error", "message": f"Judge error: {str(e)}"}

        await message_callback(session_id, "Judge", judge_response)
        yield {"type": "debater_end", "role": "Judge", "round": 0}
        yield {"type": "complete", "message": "Debate completed"}

    except Exception as e:
        yield {"type": "error", "message": f"Debate failed: {str(e)}\n{traceback.format_exc()}"}
    finally:
        active_debates.discard(session_id)
