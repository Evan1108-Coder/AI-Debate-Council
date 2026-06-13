# AI Debate Council — Desktop App

> Multi-agent debate engine: model teams argue opposing sides, challenge claims, track evidence, and produce judged verdicts with deep analytics.

![Status](https://img.shields.io/badge/status-beta-orange)
![License](https://img.shields.io/badge/license-MIT-blue)
![Backend](https://img.shields.io/badge/backend-Python%203.13%20%2B%20FastAPI-3776AB)
![Frontend](https://img.shields.io/badge/frontend-Next.js%20%2B%20React%2019-000000)
![Desktop](https://img.shields.io/badge/desktop-Electron-47848F)
![Models](https://img.shields.io/badge/models-28%20across%206%20providers-success)

> Status: beta multi-agent debate app. It can help compare arguments and evidence, but it should **not** be treated as an authority on factual, legal, medical, or financial decisions. Verdicts are structured opinions, not proof.

---

## ⚡ TL;DR — what you need to know

| | |
| --- | --- |
| **What it is** | A desktop app where AI teams (Pro vs Con) run a full structured debate and a Judge delivers an analytics-weighted verdict. |
| **Install** | Download a [release](https://github.com/Evan1108-Coder/AI-Debate-Council/releases) installer, **or** clone + `dev.py` (see [Quick Start](#-quick-start)). |
| **Requires** | Python **3.13** and Node **20+**, plus **at least one** AI provider API key in `.env`. |
| **First run** | Launch → type a topic → watch the multi-round debate stream live → read the Judge verdict + Graphs & Statistics. |
| **Two modes** | **AI vs AI** debate, and **AI vs Human** debate *training* with a coaching Debate Trainer and a persistent profile. |
| **Models** | 28 models across 6 providers (OpenAI, Anthropic, Google, Groq, MiniMax, Moonshot). Add only the **provider key** — models auto-detect. |
| **Cost** | Live per-turn / per-debate USD estimates in 9 currencies. You pay your own provider API usage; the app itself is free + MIT. |
| **This branch** | `master-app-interface` = Electron desktop (`.dmg` / `.exe`). For the browser version use [`master-website-interface`](https://github.com/Evan1108-Coder/AI-Debate-Council/tree/master-website-interface). |
| **No keys to try?** | Run the test suite — it uses mock mode, no API keys needed. |

**Who it's for:** people exploring trade-offs, stress-testing ideas, fact-checking their own reasoning, or practicing debate against an AI opponent — anyone who wants *competing* arguments instead of one agreeable answer.

**Jump to:** [Screenshots](#screenshots) · [Quick Start](#-quick-start) · [Architecture](#architecture) · [Features](#features) · [Team Roles & Flow](#team-roles--debate-flow) · [Analytics Engine](#debate-intelligence--analytics-engine) · [Chat Settings](#chat-settings-reference) · [Models](#supported-models) · [REST API](#rest-api-reference) · [WebSocket](#websocket-protocol) · [Build from Source](#building-the-desktop-app-from-source) · [Tests](#running-tests) · [Project Structure](#project-structure) · [Troubleshooting](#reference-docs)

---

## Why use AI Debate Council?

- **Forces competing arguments** instead of a single agreeable answer.
- **Tracks claims, challenges, evidence, and verdict reasoning** across a whole debate, not just a transcript.
- Supports both **AI-vs-AI exploration** and **AI-vs-human debate practice**.
- Shows **analytics and long-term debate memory** — a 10-method scoring engine and a global AI identity layer.

### Current limitations

- Model debates can still hallucinate or overweight weak evidence.
- Verdicts are structured opinions, not proof.
- Costs, latency, and quality depend on the selected model providers.

---

## Screenshots

> Note: screenshot values are illustrative, not claims or factual debate results.

### AI vs AI Debate — Judge Verdict and Cost Tracking
![Debate Session with Judge Verdict](docs/images/debate-session.png)

### Graphs & Statistics — Debate Analytics Dashboard
![Graphs and Statistics Panel](docs/images/graphs-stats.png)

### Debate Intelligence — Claims, Challenges, and Verdict Review
![Debate Intelligence Panel](docs/images/debate-intelligence.png)

### AI Debater Experiences — Global Memory Layer
![AI Debater Experiences](docs/images/ai-experiences.png)

### User Debate Profile — AI vs Human Training Dashboard
![User Debate Profile](docs/images/user-profile.png)

### Council Settings & Dark Mode
![Council Settings](docs/images/council-settings.png)
![Dark Mode](docs/images/dark-mode.png)

---

## 🚀 Quick Start

### Option A — Desktop installer (recommended)

Download a pre-built installer from the [Releases page](https://github.com/Evan1108-Coder/AI-Debate-Council/releases):

| Platform | File |
| --- | --- |
| macOS (Apple Silicon) | `AI Debate Council-1.0.0-arm64.dmg` |
| macOS (Intel) | `AI Debate Council-1.0.0.dmg` |
| Windows | `AI Debate Council Setup 1.0.0.exe` |

Prerequisites: **Python 3.13** and **Node.js 20+** installed on your system. On first launch the app prepares its bundled backend; then add at least one provider key (see below).

macOS post-install (one-time dependency setup):

```bash
cd /Applications/AI\ Debate\ Council.app/Contents/Resources/app-content
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
cp .env.example .env
# Edit .env to add at least one provider API key
```

### Option B — Run from source

```bash
git clone https://github.com/Evan1108-Coder/AI-Debate-Council.git
cd AI-Debate-Council
git checkout master-app-interface

python3.13 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

cp .env.example .env
# Edit .env — add at least one AI provider key (e.g. OPENAI_API_KEY=...)

.venv/bin/python dev.py     # one-command launcher (backend + frontend)
```

Then open **http://localhost:6001**.

### First-run walkthrough

1. **Pick / create a session** in the left sidebar (up to 10 sessions).
2. **Type a topic or question** in the message box (e.g. *"Should AI be regulated?"*).
3. The **intent classifier** decides debate vs chat; for a debate it spins up Pro & Con teams.
4. Watch the **multi-round debate stream** token-by-token through each phase.
5. Read the **Judge verdict**, then open **Graphs & Statistics** and **Debate Intelligence** to inspect the reasoning, claim ledger, and analytics.
6. Tune everything in **Chat Settings** (debaters per team, judge panel size, models per role, tone, language, cost currency…).

Full setup notes live in [SETUP.md](SETUP.md); environment variables in [ENVREADME.md](ENVREADME.md).

---

## Architecture

![System Architecture](docs/images/architecture.png)

*Three-layer architecture: the Next.js client talks over HTTP + WebSockets to a FastAPI server backed by SQLite, while a LiteLLM router dispatches LLM calls to the configured providers.*

![Debate Flow](docs/images/debate-flow.png)

*End-to-end flow: topic entry → setup → multi-round debate with up to four specialist roles per team → real-time WebSocket streaming → analytics-weighted judgment → post-debate intelligence.*

**Stack:** Backend = Python 3.13 · FastAPI · SQLite · WebSockets · LiteLLM. Frontend = Next.js · React 19 · TypeScript · Tailwind CSS. Desktop shell = Electron (background processes, no terminal window needed).

---

## Features

- **Pro and Con teams** with 1–4 debaters per team across four roles (Advocate, Rebuttal Critic, Evidence Researcher, Cross-Examiner).
- **Professional phase flow** — constructive, cross-examination, evidence, rebuttal, discussion, closing, audit, and verdict.
- **Judge AI verdict** with optional **multi-judge panel** (3 or 5) and analytics-weighted scoring.
- **AI vs Human Debate Training** — practice mode with an AI opponent, a **Debate Trainer** coach, and a persistent user profile.
- **Council Assistant** — dual-mode chat that classifies each message as debate or conversation (with an optional "always chat" override).
- **28 models across 6 providers** — add only provider keys; models auto-detect.
- **10-method analytics engine** — Bayesian inference, argument mining, game theory, ELO credibility, MoE role gating, and more (no ML deps; pure stdlib math).
- **Real-time charts** — Bayesian pie, role-weight bars, stance votes, Bayesian trend line, phase timeline, plus cross-debate session charts.
- **Long-term memory** — global **AI Debater Experiences** identity layer + per-session Claim/Challenge/Evidence ledgers.
- **Cost tracking** — per-debate and per-turn estimates in **9 currencies** with live OpenRouter pricing.
- **Dark mode** — Light, Dark, and System themes.
- **Desktop app** — Electron wrapper running invisible background servers; no terminal needed.
- **Resilient streaming** — auto-continuation on token-limit truncation; up to 3 provider retries before any output streams.

---

## Team Roles & Debate Flow

Each debate has two teams (Pro and Con) with **1–4 debaters per team**, configurable per session.

| Debaters / team | Active roles |
| --- | --- |
| 1 | Advocate |
| 2 | Advocate, Rebuttal Critic |
| 3 | + Evidence Researcher |
| 4 | + Cross-Examiner |

| Role | Job |
| --- | --- |
| **Advocate** | Build the team's central case and defend the main thesis. |
| **Rebuttal Critic** | Attack the opposing team's strongest point; shield your team. |
| **Evidence Researcher** | Add evidence, examples, context, and uncertainty notes. |
| **Cross-Examiner** | Ask pressure questions and expose contradictions. |
| **Judge Assistant** *(neutral, optional)* | Audit for missed points, unanswered claims, evidence gaps. Does not pick the winner. |
| **Judge Panelist** *(neutral, optional)* | In 3/5-judge mode each panelist votes independently before consensus. |
| **Judge** *(neutral)* | Combine transcript + audit + panel votes + analytics into the final verdict. |

**Flow:** user message → intent classify → constructive → cross-exam & evidence → discussion time → rebuttal & closing → Judge Assistant audit (optional) → Judge verdict (single or weighted panel consensus). Content streams token-by-token over WebSocket; a `StreamingSanitizer` strips any `<think>` blocks so reasoning traces never reach the UI. See [docs/TEAM_ROLES.md](docs/TEAM_ROLES.md) for discussion rules, truncation handling, and retry logic.

---

## Debate Intelligence & Analytics Engine

A lightweight engine (`backend/app/analytics.py`) scores every transcript with **standard-library math only** — no extra ML dependencies. Results stream to the UI, feed the Judge prompt, and are optionally weighted into the verdict.

| Method | What it does |
| --- | --- |
| **Ensemble Voting** | Per-role stance labels → majority + confidence-weighted vote. |
| **Bayesian Inference** | Symmetric prior updated with credibility-adjusted evidence → support/oppose/mixed probabilities. |
| **Argument Mining** | Extracts claims, evidence cues, rebuttals; flags redundant turns. |
| **Argument Graph** | Claims = nodes; Jaccard similarity builds support/attack edges; node strength adjusts. |
| **Game Theory** | Auction score lets confident, novel arguments bid for influence; Nash pressure estimates disagreement. |
| **ELO-Style Credibility** | Per-turn ELO from confidence, novelty, evidence, redundancy → 0.2–1.25 multiplier. |
| **Confidence Calibration** | Temperature scaling softens extreme confidence to avoid false certainty. |
| **Attention Mechanisms** | Top salient (non-stopword) terms surfaced to UI + Judge; topic terms double-weighted. |
| **Delphi Convergence** | Round-by-round stance comparison (1.0 = converged, 0.0 = max shift). |
| **Mixture of Experts (MoE)** | Topic keywords gate which role archetype matters most; combined with per-turn quality. |

**Graphs & Statistics panel** shows: phase timeline, metrics row (weighted vote, Bayesian leader, avg confidence, Delphi convergence), Bayesian pie, role-weight bars, stance votes, Bayesian trend line, game/graph stats, plus **cross-debate session charts** (Win Rate by Team, Cost Breakdown by Phase, Debate Duration, Messages per Role, Citation Box).

**Debate Intelligence tab** stores structured records from the real transcript: **Claim Ledger**, **Challenge & Resolution Tracker**, **Evidence Ledger**, **Judge Scorecard**, **Verdict Review** (challenge/override), and view-only **Team Rooms**. Full detail in [docs/DEBATE_INTELLIGENCE.md](docs/DEBATE_INTELLIGENCE.md).

---

## Chat Settings reference

Each session stores its own settings; changes take effect on the **next turn** — even mid-debate (e.g. debaters per team). Sections: Overall Model, Debating Flow, Debaters & Teams / Practice Agents, Council Assistant, Debate Intelligence, Judgment Quality, Prompt & Tone, Output & Display, Advanced.

### Session-level settings

| Setting | Default | Range | Description |
| --- | --- | --- | --- |
| Overall Model | none | any unlocked | Default model for all roles. |
| Debaters per team | 2 | 1–4 | Active debater roles per team. |
| Discussion Messages / Team | 3 | 1–4 | Advocate messages per team per discussion phase. |
| Debate rounds | 2 | 1–6 | Advocate-led discussion phases. |
| Judge Assistant | On | On/Off | Audit before the verdict. |
| Judge Panel Size | 1 | 1, 3, 5 | Independent panelists (3/5 = more robust, costs more). |
| Analytics Weight | 0.25 | 0–0.75 | How much analytics influences the verdict vs the AI Judge/panel. |
| Allow Verdict Challenge/Override | On | On/Off | Challenge verdict or override saved winner. |
| Temperature | 0.55 | 0.00–1.00 | Default for all roles. |
| Max tokens | 700 | 120–2000 | Default for all roles. |
| Debate tone | Academic | Academic/Casual/Formal/Aggressive | Injected into prompts. |
| Language | English | English/Chinese/Cantonese | Injected into prompts. |
| Response length | Normal | Concise/Normal/Detailed | Word-limit control. |
| Context window | 2 | 0–6 | Recent rounds included in debater prompts. |
| Auto-scroll | On | On/Off | Scroll to latest message. |
| Show timestamps | Off | On/Off | Message timestamps. |
| Show token count | Off | On/Off | Estimated token counts. |
| Show money cost | On | On/Off | Estimated API cost. |
| Cost currency | USD | USD/CNY/HKD/EUR/JPY/GBP/AUD/CAD/SGD | Display currency. |
| Show model costs | Off | On/Off | Per-model cost breakdown. |
| Show Every Message Cost | Off | On/Off | Per-message costs during debate. |
| Fact-check mode | Off | On/Off | Flag uncertain claims (reserved). |
| Export format | Markdown | Markdown/PDF/JSON | Reserved. |
| Auto-save interval | 30 | 5–300 s | Reserved. |

### Per-agent overrides

Each role (Advocate, Rebuttal Critic, Evidence Researcher, Cross-Examiner, Judge Assistant, Judge, Council Assistant, Practice Debater, Debate Trainer) can override **Model**, **Temperature**, **Max tokens**, and **Response length**. Evidence Researcher adds a **Web search** flag; Council Assistant adds an **Always On** (bypass classifier) flag. Team role settings apply to both Pro and Con. See [docs/CHAT_SETTINGS.md](docs/CHAT_SETTINGS.md).

---

## Supported Models

Add only provider API keys to `.env` — no model names needed. The app auto-detects available models.

| Provider | API Key Variable | Models |
| --- | --- | --- |
| OpenAI | `OPENAI_API_KEY` | gpt-5.5-pro, gpt-5.5, gpt-5.5-mini, gpt-5.4-pro, gpt-5.4-mini, gpt-4o, gpt-4o-mini |
| Anthropic | `ANTHROPIC_API_KEY` | claude-opus-4-7, claude-sonnet-4-7, claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5, claude-3.5-sonnet |
| Google | `GOOGLE_API_KEY` | gemini-3.1-pro, gemini-3-flash, gemini-2.5-flash-lite |
| Llama via Groq | `GROQ_API_KEY` | llama-4-maverick, llama-4-scout, llama-3.3-70b |
| MiniMax | `MINIMAX_API_KEY` | minimax-m3, minimax-m2.7, minimax-m2.5 |
| Moonshot | `MOONSHOT_API_KEY` | kimi-latest, kimi-k2-thinking, kimi-k2-turbo-preview, kimi-k2.5-vision, moonshot-v1-128k |

---

## REST API reference

Base URL: `http://localhost:8000` (backend). Selected endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Status, database path, active debate count. |
| `GET` | `/api/models` | Unlocked models, provider summaries, mock-mode status. |
| `GET` / `POST` / `DELETE` | `/api/sessions` | List / create (max 10) / delete-all (keeps memory). |
| `PATCH` / `DELETE` | `/api/sessions/{id}` | Rename / delete a session. |
| `POST` | `/api/sessions/{id}/clear-history` | Hide messages & debates (keeps memory). |
| `POST` | `/api/sessions/{id}/clear-memory` | Delete all debates & messages for a session. |
| `GET` | `/api/sessions/{id}/messages` · `/debates` | List visible messages / debates. |
| `PATCH` / `DELETE` | `/api/sessions/{id}/debates/{did}` | Rename / hide a debate. |
| `GET` / `PATCH` | `/api/sessions/{id}/settings` | Get / update session settings. |
| `GET` | `/api/sessions/{id}/analytics?debate_id=` | Analytics for latest/specified debate. |
| `GET` | `/api/sessions/{id}/intelligence?debate_id=` | Claim/Challenge/Evidence ledgers, scorecard, team rooms, verdict review. |
| `GET` | `/api/sessions/{id}/practice-state` | Whether an AI-vs-Human practice debate is active. |
| `POST` | `/api/sessions/{id}/debates/{did}/feedback` | Save post-debate user feedback. |
| `POST` | `/api/sessions/{id}/debates/{did}/verdict-review` | Save a verdict challenge / winner override. |
| `GET` / `PATCH` | `/api/council-settings` | Get / update universal Council Settings. |
| `POST` | `/api/council-settings/reset-agent-experience` | Reset universal agent identity (confirmed). |
| `GET` | `/api/ai-debater-experiences` | Global AI identity memory view. |
| `GET` | `/api/user-debate-profile` · `/overview` | Training profile / dashboard with recommendations. |
| `POST` | `/api/user-debate-profile/reset` | Reset training profile (confirmed). |
| `POST` | `/api/runtime-diary` | Record a runtime diary entry. |

Full reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md).

---

## WebSocket protocol

Endpoint: `ws://localhost:8000/ws/debates/{session_id}`.

Start: `{"type": "start_interaction", "topic": "...", "model": "model-name"}`. End a practice debate: `{"type": "end_practice_debate", "model": "model-name"}`.

Server → client events: `debate_started`, `interaction_started`, `practice_state_updated`, `team_preparation_started/completed`, `message_started`, `message_delta`, `message_replaced`, `message_completed` (with `cost_summary`), `analysis_updated`, `debate_completed`, `interaction_completed`, `error`. Full table: [docs/WEBSOCKET_PROTOCOL.md](docs/WEBSOCKET_PROTOCOL.md).

---

## Building the desktop app from source

```bash
git clone https://github.com/Evan1108-Coder/AI-Debate-Council.git
cd AI-Debate-Council
git checkout master-app-interface

python3.13 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && npx next build && cd ..
cd electron && npm install

npm run build:mac    # macOS .dmg
npm run build:win    # Windows .exe
```

---

## Running tests

```bash
python3.13 -m unittest discover -s backend/tests -v
```

Tests run in **mock mode** and require no API keys (`test_analytics`, `test_costing`, `test_debate_architecture`, `test_model_registry`, `test_session_naming`, `test_session_settings`).

---

## Project structure

```text
backend/   FastAPI app — main.py, debate.py (DebateManager), database.py,
           model_registry.py, schemas.py, config.py, analytics.py (10-method
           engine), costing.py, runtime_diary.py (secret-scrubbing logs), tests/
frontend/  Next.js — components/ (DebateRoom, GlobalWorkspace, Sidebar),
           lib/api.ts (REST + WS client), types/, Tailwind config
electron/  main.js (background servers + splash), electron-builder config, icons/
dev.py     one-command local launcher (backend + frontend)
```

Full tree: [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md).

---

## Reference docs

| Topic | Document |
| --- | --- |
| REST API endpoints | [docs/API_REFERENCE.md](docs/API_REFERENCE.md) |
| WebSocket protocol | [docs/WEBSOCKET_PROTOCOL.md](docs/WEBSOCKET_PROTOCOL.md) |
| Team roles & debate flow | [docs/TEAM_ROLES.md](docs/TEAM_ROLES.md) |
| Debate intelligence & analytics | [docs/DEBATE_INTELLIGENCE.md](docs/DEBATE_INTELLIGENCE.md) |
| Chat settings reference | [docs/CHAT_SETTINGS.md](docs/CHAT_SETTINGS.md) |
| Project structure | [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) |
| Setup guide | [SETUP.md](SETUP.md) |
| Environment variables | [ENVREADME.md](ENVREADME.md) |
| Troubleshooting | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Security policy | [SECURITY.md](SECURITY.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

## Branches

| Branch | Description |
| --- | --- |
| `master-website-interface` | Web application — runs in the browser via `dev.py`. |
| `master-app-interface` | Desktop application — Electron wrapper for macOS and Windows. |

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Real visual snapshot

These visuals are generated from the actual repository structure and project workflow, not placeholders.

![Repository file mix](docs/assets/repo-file-mix.svg)

![Project workflow](docs/assets/workflow.svg)
