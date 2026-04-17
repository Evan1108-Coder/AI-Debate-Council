# AI Debate Council

AI Debate Council is a full-stack web application where two AI teams — Pro and Con — debate any topic you choose in real time. Each team fields up to four specialist debaters with distinct roles. After the debate, an optional Judge Assistant audits the transcript for missed points, and a Judge AI delivers a final verdict. The entire exchange streams token by token over WebSockets so you can watch it unfold live.

The backend is Python 3.13, FastAPI, SQLite, WebSockets, and LiteLLM. The frontend is Next.js, React, TypeScript, and Tailwind CSS.

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Supported Models](#supported-models)
- [Team Roles and Debate Flow](#team-roles-and-debate-flow)
- [Debate Intelligence and Analytics](#debate-intelligence-and-analytics)
- [Chat Settings](#chat-settings)
- [Session and Debate Management](#session-and-debate-management)
- [API Reference](#api-reference)
- [WebSocket Protocol](#websocket-protocol)
- [Quick Start](#quick-start)
- [Running Tests](#running-tests)
- [Development Notes](#development-notes)
- [Related Documentation](#related-documentation)
- [License](#license)

## Features

### Debate System

- **Pro and Con teams** with 1 to 4 debaters per team, configurable per chat.
- **Four team roles**: Lead Advocate, Rebuttal Critic, Evidence Researcher, and Cross-Examiner. Each role has a distinct system prompt, job description, and default behavior.
- **Bid-based turn selection**: A moderator LLM (or local heuristic fallback) chooses who speaks next based on urgency, intent, and what was just said — not a fixed rotation.
- **Optional Judge Assistant**: Before the final verdict, a neutral Judge Assistant audits the debate for missed points, unanswered claims, evidence gaps, contradictions, and useful statistics for the Judge.
- **Judge AI verdict**: The Judge receives the full transcript, the Judge Assistant audit, and live analytics, then delivers a structured six-part verdict naming a winner.
- **Maximum 3 active debates** running concurrently across all sessions.

### Chat and Council Assistant

- **Dual-mode interaction**: The system automatically classifies each message as "debate" or "chat" using an LLM intent classifier with heuristic fallback. Debate-like messages trigger the full council; normal messages go to the Council Assistant.
- **Council Assistant**: A single chat agent that answers follow-up questions, explains past debate results, and handles non-debate conversations using the session's message history as memory.
- **Always On mode**: Optionally force all messages through the Council Assistant, bypassing the intent classifier.

### Model Support

- **21 models across 6 providers**: OpenAI, Anthropic, Google, Groq (Llama), MiniMax, and Moonshot.
- **Automatic model detection**: Add a provider API key to `.env` and all models from that provider appear in the dropdown. No model names go in `.env`.
- **Per-agent model overrides**: Each role (Lead Advocate, Rebuttal Critic, etc.) can use a different model, or fall back to the session's Overall Model.
- **Mock mode**: Set `MOCK_LLM_RESPONSES=true` to test the full UI flow without real API calls.

### Analytics and Intelligence

- **10-method debate intelligence panel** built into the Graphs & Statistics tab: ensemble voting, Bayesian inference, argument mining, game theory, argument graphs, attention mechanisms, confidence calibration, Delphi convergence, Mixture of Experts, and ELO-style credibility scoring.
- **Real-time analytics updates** streamed after each debater turn.
- **Visual charts**: Bayesian pie chart, role weight bars, stance vote bars, Bayesian trend line chart, and argument mining details.
- **Per-debate statistics**: Switch between saved debates in the stats panel.

### Session Management

- **Up to 10 chat sessions** at a time.
- **Default naming**: Sessions increment as `Debate Session #1`, `Debate Session #2`, etc. Deleted numbers are never reused unless every session is deleted, which resets the counter.
- **Rename and delete** sessions and individual debates from Chat Settings.
- **Clear Chat History**: Hides messages and debate graphs while preserving hidden memory for follow-up questions.
- **Clear Chat Memory**: Permanently removes all messages and debates from a session.

### Per-Chat Settings

- Overall Model selection (applies to all roles by default).
- Debaters per team (1–4).
- Judge Assistant toggle (on/off, recommended on).
- Per-agent settings: model, temperature (0–1), max tokens (120–2000), response length (Concise/Normal/Detailed), web search toggle for Evidence Researcher, Always On toggle for Council Assistant.
- Debate tone (Academic, Casual, Formal, Aggressive).
- Language (English, Chinese, Cantonese).
- Context window (0–6 rounds of debate history included in prompts).
- Debate rounds (1–6).
- Auto-scroll, show timestamps, show token count.
- Fact-check mode (reserved for future tool integration).
- Export format (Markdown, PDF, JSON — reserved).
- Auto-save interval (5–300 seconds).

## Architecture Overview

```text
Browser (Next.js on port 6001)
   |
   |-- REST API calls (sessions, models, settings, analytics)
   |-- WebSocket connection (debates, chat, streaming)
   |
FastAPI backend (port 8000)
   |
   |-- LiteLLM (routes to OpenAI, Anthropic, Google, Groq, MiniMax, Moonshot)
   |-- SQLite database (sessions, settings, debates, messages)
   |-- Analytics engine (10 scoring methods, no ML dependencies)
```

The backend is a single Python process. All state lives in SQLite. The active-debate limit (3) and session limit (10) are enforced in-process. For production use, run a single worker or move the counters to shared storage like Redis.

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, REST endpoints, WebSocket handler
│   │   ├── debate.py            # DebateManager: turn selection, streaming, prompts
│   │   ├── database.py          # SQLite schema, session/debate/message CRUD
│   │   ├── model_registry.py    # MODEL_MAP, provider detection, SupportedModel
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── config.py            # Settings from environment variables
│   │   └── analytics.py         # 10-method debate analysis engine
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_analytics.py
│   │   ├── test_debate_architecture.py
│   │   ├── test_model_registry.py
│   │   ├── test_session_naming.py
│   │   └── test_session_settings.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── DebateRoom.tsx       # Main debate UI: chat, stats, settings panels
│   │   └── Sidebar.tsx          # Session list sidebar
│   ├── lib/
│   │   └── api.ts               # REST and WebSocket client functions
│   ├── types/
│   │   └── index.ts             # TypeScript type definitions
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.mjs
│   └── tsconfig.json
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── SETUP.md
├── ENVREADME.md
└── TROUBLESHOOTING.md
```

## Supported Models

No model names belong in `.env`. Add only provider API keys. The app detects which models are available by checking which API key environment variables are present.

One provider key unlocks every model listed for that provider. For example, `OPENAI_API_KEY` unlocks all four OpenAI models. The backend has a built-in `MODEL_MAP` in `backend/app/model_registry.py` that already knows every model name, provider, and LiteLLM routing string.

`GET /api/models` returns a `models` list containing only unlocked models. The frontend uses that list for all dropdowns. If no provider keys are set, the real model dropdown is empty and debates cannot start (unless mock mode is enabled).

| Provider | API Key Variable | Models Unlocked |
| --- | --- | --- |
| OpenAI | `OPENAI_API_KEY` | `gpt-5.4-pro`, `gpt-5.4-mini`, `gpt-4o`, `gpt-4o-mini` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-3.5-sonnet` |
| Google | `GOOGLE_API_KEY` | `gemini-3.1-pro`, `gemini-3-flash`, `gemini-2.5-flash-lite` |
| Llama via Groq | `GROQ_API_KEY` | `llama-4-maverick`, `llama-4-scout`, `llama-3.3-70b` |
| MiniMax | `MINIMAX_API_KEY` | `minimax-m2.7`, `minimax-m2.5-lightning` |
| Moonshot | `MOONSHOT_API_KEY` | `kimi-latest`, `kimi-k2-thinking`, `kimi-k2-turbo-preview`, `kimi-k2.5-vision`, `moonshot-v1-128k` |

**Total: 21 models across 6 providers.**

### Placeholder Detection

The backend ignores placeholder values in API keys. If you leave a key set to `your_key_here`, `changeme`, `none`, `null`, or `false`, the provider will not be activated.

## Team Roles and Debate Flow

### Team Structure

Each debate has two teams (Pro and Con) with 1 to 4 debaters per team. The number of debaters is configurable per chat session in Chat Settings.

| Debaters Per Team | Active Roles |
| --- | --- |
| 1 | Lead Advocate |
| 2 | Lead Advocate, Rebuttal Critic |
| 3 | Lead Advocate, Rebuttal Critic, Evidence Researcher |
| 4 | Lead Advocate, Rebuttal Critic, Evidence Researcher, Cross-Examiner |

### Role Descriptions

| Role | Job |
| --- | --- |
| **Lead Advocate** | Build the team's central case, keep the argument coherent, and defend the main thesis. |
| **Rebuttal Critic** | Attack the opposing team's strongest point and protect your team from direct criticism. |
| **Evidence Researcher** | Add evidence, examples, missing context, and careful uncertainty notes for your team. |
| **Cross-Examiner** | Ask pressure questions, expose contradictions, and force the other team to answer clearly. |
| **Judge Assistant** (neutral, optional) | Audit the debate for missed points, unanswered claims, evidence gaps, statistics, and scoring risks. Does not choose the final winner. |
| **Judge** (neutral) | Use the debate transcript, Judge Assistant audit, and analytics to make the final decision. |

### Debate Flow

1. **User sends a message.** The intent classifier determines whether to start a debate or a chat.
2. **Pro Lead Advocate opens** the affirmative case.
3. **Con Lead Advocate responds** with the opposing case.
4. **Moderator selects turns.** For each subsequent turn, a moderator LLM (or local heuristic fallback) picks the best speaker based on urgency, intent, and the state of the debate. This is not a fixed rotation — agents "bid" for the floor.
5. **Turns continue** until the configured number of rounds completes (rounds × active debaters = total turns).
6. **Judge Assistant audits** (if enabled) the full transcript and analytics.
7. **Judge delivers verdict** with six parts: best affirmative argument, best skeptical argument, best evidence or research need, analytics agreement/disagreement, clear winner, and why.

### Turn Selection

The bid-based system scores each agent on:

- Whether they have spoken yet (new voices get a bonus).
- Whether the opposing team just made a point (cross-team response urgency).
- Whether there is a direct question to answer.
- Archetype-specific bonuses (Rebuttal Critic gets urgency against opposing claims, Cross-Examiner gets urgency when few recent questions exist, etc.).
- Penalties for speaking too recently or for same-team monopoly.

If the moderator LLM is available, it overrides the local heuristic and can also signal "END" to stop the debate early if further turns would be repetitive.

### Streaming

All debate content streams token by token over WebSocket. The frontend renders each delta as it arrives. A `StreamingSanitizer` strips any `<think>` blocks that some models emit, so reasoning traces never appear in the UI.

### Truncation Handling

If a model response hits the max-token limit (`finish_reason: "length"`), the system automatically sends a continuation request to the same model, asking it to pick up where it stopped. If the continuation also truncates, a notice is appended suggesting the user increase the role's max tokens in Chat Settings.

### Retry Logic

Provider errors (overloaded, rate limit, timeout, connection errors) are retried up to 3 times with increasing delays, but only if no output has been streamed yet. Once output has started streaming, the error is surfaced to the user.

## Debate Intelligence and Analytics

The backend includes a lightweight analytics engine in `backend/app/analytics.py`. It requires no extra ML dependencies — all scoring is done with Python standard library math. Each debate transcript is analyzed and the results are streamed to the frontend and included in the Judge prompt.

| Method | Description |
| --- | --- |
| **Ensemble Voting** | Each role gets a stance label (support, oppose, mixed). The app reports both majority vote and confidence-weighted vote. |
| **Bayesian Inference** | A symmetric prior is updated with confidence-weighted, credibility-adjusted stance evidence. Produces probabilities for support, oppose, and mixed. |
| **Argument Mining** | Heuristics extract claims (sentences with "should", "is", "must", etc.), evidence cues ("because", "study", "data", etc.), rebuttals ("however", "but", "counter", etc.), and flags redundant turns. |
| **Argument Graph** | Claims become nodes. Similar claims (by Jaccard similarity) create support edges (same stance) or attack edges (opposing stance). Node strength is adjusted by edge relationships. |
| **Game Theory** | An auction score lets high-confidence, novel arguments bid for influence. Nash pressure estimates the level of disagreement. |
| **ELO-Style Credibility** | Each turn earns an ELO rating based on confidence, novelty, evidence count, and redundancy. Ratings are normalized to a 0.2–1.25 credibility multiplier. |
| **Confidence Calibration** | Raw confidence is computed from claim count, evidence count, assertive terms, and hedge terms. Temperature scaling softens extreme values to avoid false certainty. |
| **Attention Mechanisms** | Frequent high-salience terms from the transcript (excluding stopwords) become attention terms shown in the UI and available to the Judge. Topic-related terms get double weight. |
| **Delphi Convergence** | Round-by-round stance distributions are compared. Convergence measures how much the debate has stabilized (1.0 = fully converged, 0.0 = maximum shift). |
| **Mixture of Experts (MoE)** | Deterministic role gates weight which archetype should matter most based on topic keywords (e.g., "evidence"/"data" boosts researchers, "risk"/"safety" boosts critics). Gate weights are combined with per-turn quality scores. |

### Analytics in the UI

The Graphs & Statistics panel shows:

- **Metrics row**: Weighted vote, Bayesian leader, average confidence, Delphi convergence.
- **Bayesian pie chart**: Support vs. oppose vs. mixed probabilities.
- **Role weights bar chart**: MoE-normalized weights per active role.
- **Stance votes bar chart**: Weighted vote totals per stance.
- **Bayesian trend line chart**: Round-by-round probability history.
- **Game and graph stats**: Auction winner, Nash pressure, node count, edge counts.
- **Argument mining details**: Evidence cue count, rebuttal cue count, redundant turn count, strongest mined claims.
- **Attention terms**: Top 8 salient terms from the transcript.

## Chat Settings

Each session stores its own settings. Changes take effect on the next turn — even mid-debate for settings like debaters per team. Settings are accessible from the Chat Settings panel in the UI.

### Session-Level Settings

| Setting | Default | Range | Description |
| --- | --- | --- | --- |
| Overall Model | (none) | Any unlocked model | Default model for all roles in this chat. |
| Debaters per team | 3 | 1–4 | Number of debater roles active per team. |
| Judge Assistant | On | On/Off | Whether the Judge Assistant audits before the verdict. |
| Temperature | 0.55 | 0.00–1.00 | Default temperature for all roles. |
| Max tokens | 700 | 120–2000 | Default max tokens for all roles. |
| Debate tone | Academic | Academic, Casual, Formal, Aggressive | Injected into all system prompts. |
| Language | English | English, Chinese, Cantonese | Injected into all system prompts. |
| Response length | Normal | Concise, Normal, Detailed | Controls word limits in debater prompts. |
| Context window | 2 | 0–6 | How many rounds of recent debate history are included in debater prompts. |
| Debate rounds | 2 | 1–6 | Number of full rounds before judging. |
| Auto-scroll | On | On/Off | Auto-scroll to latest message. |
| Show timestamps | Off | On/Off | Show message timestamps. |
| Show token count | Off | On/Off | Show estimated token counts. |
| Fact-check mode | Off | On/Off | Flag uncertain claims (reserved for tool integration). |
| Export format | Markdown | Markdown, PDF, JSON | Reserved for future export feature. |
| Auto-save interval | 30 | 5–300 seconds | Reserved for future auto-save feature. |

### Per-Agent Settings

Each of the 7 agent roles (Lead Advocate, Rebuttal Critic, Evidence Researcher, Cross-Examiner, Judge Assistant, Judge, Council Assistant) can override:

| Setting | Default | Description |
| --- | --- | --- |
| Model | Use overall model | Override model for this role only. |
| Temperature | Inherits session default | Override temperature for this role. |
| Max tokens | Inherits session default | Override max tokens for this role. |
| Response length | Inherits session default | Override word limit for this role. |
| Web search | Off | Evidence Researcher only: flag for web search integration. |
| Always On | Off | Council Assistant only: bypass intent classifier, always use chat mode. |

Team role settings (Lead Advocate, Rebuttal Critic, etc.) apply to both the Pro and Con versions of that role.

## Session and Debate Management

### Sessions

- Create up to 10 sessions. Attempting to create an 11th returns HTTP 409.
- Default names: `Debate Session #1`, `Debate Session #2`, etc. Counter is monotonic — deleted numbers are never reused while any session exists.
- If all sessions are deleted, the counter resets. The next session will be `Debate Session #1`.
- Rename sessions (1–80 characters) from Chat Settings.
- Delete a session to remove all its debates, messages, and settings.

### Debates Within Sessions

- Each session can contain multiple debates and chat interactions.
- Debates are named `Debate #1`, `Debate #2`, etc. within each session.
- Chat interactions (Council Assistant responses) are tracked separately and do not appear in the debate list.
- Rename or delete individual debate statistics from Chat Settings. Deleting a debate's statistics removes only its graphs and analytics — the messages remain in the chat transcript.

### History and Memory

- **Clear Chat History**: Hides all visible messages and debate graphs. Hidden messages are still used as memory for follow-up Council Assistant responses.
- **Clear Chat Memory**: Permanently deletes all debates and messages for the session. The session itself remains.

## API Reference

### REST Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check. Returns status, database path, active debate count. |
| `GET` | `/api/models` | List unlocked models, provider summaries, mock mode status. |
| `GET` | `/api/sessions` | List all sessions, sorted by last updated. |
| `POST` | `/api/sessions` | Create a new session. Returns 409 if at the 10-session limit. |
| `PATCH` | `/api/sessions/{session_id}` | Rename a session. Body: `{"name": "New Name"}`. |
| `DELETE` | `/api/sessions/{session_id}` | Delete a session and all its data. |
| `POST` | `/api/sessions/{session_id}/clear-history` | Hide visible messages and debates (preserves memory). |
| `POST` | `/api/sessions/{session_id}/clear-memory` | Delete all debates and messages for a session. |
| `GET` | `/api/sessions/{session_id}/messages` | List visible messages for a session. |
| `GET` | `/api/sessions/{session_id}/debates` | List visible debates for a session. |
| `PATCH` | `/api/sessions/{session_id}/debates/{debate_id}` | Rename a debate. Body: `{"name": "New Name"}`. |
| `DELETE` | `/api/sessions/{session_id}/debates/{debate_id}` | Hide a debate's statistics (messages remain). |
| `GET` | `/api/sessions/{session_id}/settings` | Get session settings. |
| `PATCH` | `/api/sessions/{session_id}/settings` | Update session settings. Body: partial settings object. |
| `GET` | `/api/sessions/{session_id}/analytics?debate_id=...` | Get analytics for a session's latest or specified debate. |

### WebSocket

| Path | Description |
| --- | --- |
| `ws://localhost:8000/ws/debates/{session_id}` | Bidirectional WebSocket for debates and chat. |

Send `{"type": "start_interaction", "topic": "...", "model": "model-name"}` to begin. The backend classifies intent and runs either a debate or a chat, streaming events back.

## WebSocket Protocol

### Client to Server

```json
{
  "type": "start_interaction",
  "topic": "Should AI be regulated?",
  "model": "claude-sonnet-4-6"
}
```

### Server to Client Events

| Event Type | Description |
| --- | --- |
| `debate_started` | Debate created. Includes debate record, assignments, judge info. |
| `interaction_started` | Chat mode started. Includes mode and selected model. |
| `message_started` | A new message is about to stream. Includes speaker, role, model, round. |
| `message_delta` | A token chunk for the current stream. |
| `message_completed` | A message finished streaming. Includes the saved message record. |
| `analysis_updated` | Analytics recalculated after a debater turn. |
| `debate_completed` | Debate finished. Includes judge summary and active debate count. |
| `interaction_completed` | Chat finished. |
| `error` | An error occurred. Includes error message string. |

## Quick Start

Read [SETUP.md](SETUP.md) for detailed macOS and Windows instructions.

Short version:

```bash
# Terminal 1: Backend
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
cp .env.example .env
# Edit .env to add at least one provider API key
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Using `.venv/bin/python -m uvicorn` is the most reliable local command because it uses the Uvicorn installed inside this project's virtual environment, even if the plain `uvicorn` command is not on your shell PATH.

```bash
# Terminal 2: Frontend
cd frontend
npm install
npm run dev -- -p 6001
```

Open `http://localhost:6001`.

## Running Tests

The backend includes regression tests for session naming, model registry, session settings, analytics, and debate architecture.

```bash
# Run all tests
python3.13 -m unittest discover -s backend/tests -v

# Run individual test modules
python3.13 -m unittest backend.tests.test_session_naming -v
python3.13 -m unittest backend.tests.test_model_registry -v
python3.13 -m unittest backend.tests.test_session_settings -v
python3.13 -m unittest backend.tests.test_analytics -v
python3.13 -m unittest backend.tests.test_debate_architecture -v
```

Tests use mock mode and do not require API keys.

## Development Notes

- **Backend API**: `http://localhost:8000`
- **Backend health check**: `http://localhost:8000/health`
- **Frontend dev server**: `http://localhost:6001`
- **SQLite database default path**: `backend/data/debate_council.db`
- **WebSocket route**: `ws://localhost:8000/ws/debates/{session_id}`
- **Model check**: `http://localhost:8000/api/models`

For local UI testing without real model calls, set `MOCK_LLM_RESPONSES=true` in `.env` and restart the backend.

The backend loads `.env` from the project root first, then `backend/.env` as an override. Shell-level environment variables are overridden by the `.env` files to prevent stale keys from silently unlocking providers.

## Related Documentation

| Document | Description |
| --- | --- |
| [SETUP.md](SETUP.md) | Step-by-step installation for macOS and Windows. |
| [ENVREADME.md](ENVREADME.md) | Detailed explanation of every environment variable. |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Solutions for every known issue. |
| [LICENSE](LICENSE) | MIT License. |

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
