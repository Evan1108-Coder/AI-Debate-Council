# AI Debate Council - MultiAI System

A full-stack multi-AI debate platform where multiple AI debaters argue a topic from different perspectives, culminating in a Judge's verdict. Powered by 16+ AI models via LiteLLM, with real-time WebSocket streaming and a ChatGPT-style interface.

## What It Does

You enter a debate topic. Four AI debaters -- each with a distinct role -- take turns arguing over multiple rounds. A Judge then delivers a final verdict weighing all arguments. The entire debate streams in real-time to a clean, modern UI.

### Debater Roles

| Role | Purpose |
|------|---------|
| **Advocate** | Argues **in favor** of the topic with evidence and persuasive reasoning |
| **Critic** | Argues **against** the topic, identifying weaknesses and risks |
| **Researcher** | Provides **factual context**, data, studies, and expert opinions |
| **Devil's Advocate** | Challenges **all sides** with unexpected angles and edge cases |
| **Judge** | Delivers a **balanced verdict** after evaluating all arguments |

## Features

- **Multi-Round Debates** -- Configure 1 to 5 rounds per debate for deeper discussion
- **16 AI Models** -- Switch between OpenAI, Anthropic, Google, Llama, and MiniMax models
- **Real-Time Streaming** -- Watch each debater's response appear token by token via WebSocket
- **ChatGPT-Style Sidebar** -- Manage up to 10 debate sessions with rename and delete
- **Concurrent Debates** -- Run up to 3 debates simultaneously
- **Persistent History** -- All debates stored in SQLite; revisit past sessions anytime
- **Session Numbering** -- Auto-incrementing names ("Debate Session #1", "#2", ...) that reset only when all sessions are deleted

## Supported Models

| Provider | Models |
|----------|--------|
| **OpenAI** | gpt-5.4-pro, gpt-5.4-mini, gpt-4o, gpt-4o-mini |
| **Anthropic** | claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5, claude-3.5-sonnet |
| **Google** | gemini-3.1-pro, gemini-3-flash, gemini-2.5-flash-lite |
| **Llama (via Groq)** | llama-4-maverick, llama-4-scout, llama-3.3-70b |
| **MiniMax** | minimax-m2.7, minimax-m2.5-lightning |

## Tech Stack

- **Backend:** Python FastAPI with async WebSocket support
- **Frontend:** Next.js 16 (App Router) + TypeScript + Tailwind CSS
- **Database:** SQLite with WAL mode via aiosqlite
- **Model Routing:** LiteLLM for unified access to all AI providers
- **Real-Time:** WebSocket streaming for token-by-token debate output

## Architecture

```
Frontend (Next.js :3000)          Backend (FastAPI :8000)
┌──────────────────────┐          ┌──────────────────────┐
│  Sidebar             │  REST    │  /api/sessions       │
│  ├─ Session list     │◄────────►│  /api/models         │
│  ├─ New/Rename/Delete│          │  /api/sessions/:id   │
│                      │          │                      │
│  ChatArea            │  WS      │  /ws/debate/:id      │
│  ├─ Topic input      │◄────────►│  ├─ Debate Engine    │
│  ├─ Model selector   │ stream   │  │  ├─ Advocate      │
│  ├─ Message display  │          │  │  ├─ Critic        │
│  └─ Round indicator  │          │  │  ├─ Researcher    │
│                      │          │  │  ├─ Devil's Adv.  │
│                      │          │  │  └─ Judge         │
│                      │          │  └─ LiteLLM ─► APIs  │
└──────────────────────┘          └──────────────────────┘
                                           │
                                     SQLite (WAL)
```

## Project Structure

```
AI-Debate-Council/
├── backend/
│   ├── main.py              # FastAPI app, REST + WebSocket endpoints
│   ├── database.py          # SQLite setup, session counter logic
│   ├── models.py            # Pydantic schemas, LiteLLM model map
│   ├── debate.py            # Debate engine, role prompts, streaming
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Backend env template
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router (layout, page)
│   │   ├── components/      # Sidebar, ChatArea
│   │   └── lib/             # API client, TypeScript types
│   ├── .env.example         # Frontend env template
│   └── package.json
├── .env.example             # Root env template (same as backend)
├── README.md                # This file
├── ENVREADME.md               # Detailed environment variable guide
├── SETUP.md                 # Step-by-step installation guide
├── TROUBLESHOOTING.md       # Common issues and fixes
└── LICENSE                  # MIT License
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/models` | List all available AI models |
| `GET` | `/api/sessions` | List all debate sessions |
| `POST` | `/api/sessions` | Create a new debate session |
| `GET` | `/api/sessions/:id` | Get a specific session |
| `PATCH` | `/api/sessions/:id/rename` | Rename a session |
| `PATCH` | `/api/sessions/:id/model` | Change the model for a session |
| `DELETE` | `/api/sessions/:id` | Delete a session |
| `GET` | `/api/sessions/:id/messages` | Get all messages in a session |
| `WS` | `/ws/debate/:id` | WebSocket endpoint for live debate |

## Getting Started

See **[SETUP.md](SETUP.md)** for full installation and setup instructions.

See **[ENVREADME.md](ENVREADME.md)** for detailed information about environment variables and API keys.

See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** if you run into issues.

## License

MIT License -- see [LICENSE](LICENSE) for details.

## Author

Built by Evan Lu
