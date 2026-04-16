# AI Debate Council

AI Debate Council is a full-stack web app where Pro and Con AI teams debate a user topic in real time, then a Judge Assistant can audit the debate before the Judge picks a winner.

The backend uses Python 3.13, FastAPI, SQLite, WebSockets, and LiteLLM. The frontend uses Next.js, React, TypeScript, and Tailwind CSS.

## Features

- Pro and Con teams with 1 to 4 debaters per team.
- Team roles: Lead Advocate, Rebuttal Critic, Evidence Researcher, and Cross-Examiner.
- Optional Judge Assistant for missed points, unanswered claims, evidence gaps, and statistics.
- Judge AI verdict after the debate.
- Bid-based turn selection so agents respond when they have a useful disagreement, answer, question, or addition.
- Real-time streamed responses over WebSockets.
- Automatic model detection from provider API keys.
- Model dropdown with only unlocked models.
- Per-chat Overall Model selection, with optional model overrides and generation settings per agent role.
- Role behavior comes from different system prompts and saved chat settings.
- Debate intelligence panel with voting, Bayesian aggregation, argument mining, confidence, convergence, graph, game-theory, and MoE-style scores.
- Maximum 3 active debates at the same time.
- Chat-style session sidebar.
- Maximum 10 sessions at the same time.
- Default names increment as `Debate Session #1`, `Debate Session #2`, and so on.
- Deleted numbers are not reused unless every chat is deleted, which resets the counter.
- Rename and delete controls inside each chat's Chat Settings panel.

## Project Structure

```text
.
+-- backend/
|   +-- app/
|   |   +-- main.py
|   |   +-- debate.py
|   |   +-- database.py
|   |   +-- model_registry.py
|   |   +-- schemas.py
|   |   +-- config.py
|   +-- requirements.txt
|   +-- .env.example
+-- frontend/
|   +-- app/
|   +-- components/
|   +-- lib/
|   +-- types/
|   +-- package.json
+-- .env.example
+-- SETUP.md
+-- ENVREADME.md
+-- TROUBLESHOOTING.md
```

## Supported Models

No model names belong in `.env`. Add only provider API keys. The app detects which models are available by checking which API key variables are present.

One provider key unlocks every model listed for that provider. For example, `OPENAI_API_KEY` unlocks all four OpenAI models in the table. `ANTHROPIC_API_KEY` unlocks all four Anthropic models, and so on.

The backend has a built-in `MODEL_MAP` in `backend/app/model_registry.py`. It already knows every model name and provider route:

- `gpt-4o` uses OpenAI.
- `claude-sonnet-4-6` uses Anthropic.
- `llama-4-maverick` uses Groq.

`GET /api/models` returns a `models` list containing only unlocked models. The frontend uses that list for the dropdown. If no provider keys are set, the real model dropdown is empty and debates cannot start.

| Provider | API key variable | Models |
| --- | --- | --- |
| OpenAI | `OPENAI_API_KEY` | `gpt-5.4-pro`, `gpt-5.4-mini`, `gpt-4o`, `gpt-4o-mini` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-3.5-sonnet` |
| Google | `GOOGLE_API_KEY` | `gemini-3.1-pro`, `gemini-3-flash`, `gemini-2.5-flash-lite` |
| Llama via Groq | `GROQ_API_KEY` | `llama-4-maverick`, `llama-4-scout`, `llama-3.3-70b` |
| MiniMax | `MINIMAX_API_KEY` | `minimax-m2.7`, `minimax-m2.5-lightning` |
| Moonshot | `MOONSHOT_API_KEY` | `kimi-latest`, `kimi-k2-thinking`, `kimi-k2-turbo-preview`, `kimi-k2.5-vision`, `moonshot-v1-128k` |

## Debate Intelligence

The backend includes a lightweight analytics layer in `backend/app/analytics.py`. It does not require extra ML dependencies. It turns each debate transcript into structured signals that are streamed to the frontend and included in the Judge prompt.

| Method | How it is used |
| --- | --- |
| Ensemble voting | Each role gets a stance label. The app reports majority and confidence-weighted votes. |
| Game theory and mechanism design | A simple auction score lets high-confidence, novel arguments bid for influence. Nash pressure estimates disagreement. |
| Bayesian inference | A symmetric prior is updated with confidence-weighted stance evidence. |
| Natural language processing | Heuristics extract claims, evidence cues, rebuttals, stance, and redundant arguments. |
| Reinforcement learning inspired scoring | ELO-style credibility scores reward evidence, novelty, and calibrated confidence. |
| Argument graphs | Claims become nodes. Similar claims create support edges; opposing claims create attack edges. |
| Attention mechanisms | Frequent high-salience terms become attention terms for the Judge and UI. |
| Confidence calibration | Confidence is softened with temperature scaling so scores avoid false certainty. |
| Delphi method | Round-by-round stance distributions are compared to track convergence. |
| Mixture of Experts | Deterministic role gates weight which role should matter most for the topic. |

## Quick Start

Read [SETUP.md](SETUP.md) for macOS and Windows instructions.

Short version:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
cp .env.example .env
uvicorn backend.app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev -- -p 6001
```

Open `http://localhost:6001`.

## Development Notes

- Backend API: `http://localhost:8000`
- Backend health check: `http://localhost:8000/health`
- Frontend: `http://localhost:6001`
- SQLite database default path: `backend/data/debate_council.db`
- WebSocket route: `ws://localhost:8000/ws/debates/{session_id}`

For local UI testing without real model calls, set `MOCK_LLM_RESPONSES=true` in `.env`.

Run backend regression tests:

```bash
python3.13 -m unittest backend.tests.test_session_naming backend.tests.test_model_registry backend.tests.test_session_settings backend.tests.test_analytics
```
