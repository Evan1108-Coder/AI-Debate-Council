# AI Debate Council - MultiAI System

A multi-AI debate platform where 4 AI debaters (Advocate, Critic, Researcher, Devil's Advocate) argue a topic from different perspectives, followed by a Judge's verdict. Supports 16+ AI models via LiteLLM.

## Features

- **4 Debaters + Judge** - Each with a unique perspective and role
- **16 AI Models** - OpenAI, Anthropic, Google, Llama, MiniMax via LiteLLM
- **Real-time Streaming** - Watch the debate unfold via WebSocket
- **Multi-round Debates** - Configure 1-5 rounds per debate
- **ChatGPT-style UI** - Sidebar with session management
- **Up to 3 Concurrent Debates** - Run multiple debates simultaneously
- **Up to 10 Chat Sessions** - With rename and delete support

## Debater Roles

| Role | Purpose |
|------|---------|
| Advocate | Argues **in favor** of the topic |
| Critic | Argues **against** the topic |
| Researcher | Provides **factual context** and evidence |
| Devil's Advocate | Challenges **all sides** with contrarian views |
| Judge | Delivers a **balanced verdict** |

## Supported Models

**OpenAI:** gpt-5.4-pro, gpt-5.4-mini, gpt-4o, gpt-4o-mini
**Anthropic:** claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5, claude-3.5-sonnet
**Google:** gemini-3.1-pro, gemini-3-flash, gemini-2.5-flash-lite
**Llama (Groq):** llama-4-maverick, llama-4-scout, llama-3.3-70b
**MiniMax:** minimax-m2.7, minimax-m2.5-lightning

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm

### 1. Clone the repository

```bash
git clone https://github.com/Evan1108-Coder/AI-Debate-Council.git
cd AI-Debate-Council
```

### 2. Set up the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your API keys
```

You need at least **one** API key to get started. For example, just an `OPENAI_API_KEY` will let you use GPT models.

### 4. Start the backend

```bash
python main.py
```

The API server starts at `http://localhost:8000`.

### 5. Set up the frontend

```bash
cd ../frontend
npm install
```

### 6. Start the frontend

```bash
npm run dev
```

The frontend starts at `http://localhost:3000`.

### 7. Open the app

Visit `http://localhost:3000` in your browser. Create a new debate session, pick a model, enter a topic, and watch the debate unfold!

## Project Structure

```
AI-Debate-Council/
├── backend/
│   ├── main.py           # FastAPI app with REST + WebSocket endpoints
│   ├── database.py       # SQLite database setup and helpers
│   ├── models.py         # Pydantic models and LiteLLM model mapping
│   ├── debate.py         # Debate engine (roles, prompts, streaming)
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router pages
│   │   ├── components/   # React components (Sidebar, ChatArea)
│   │   └── lib/          # API client, types
│   ├── .env.example      # Frontend env template
│   └── package.json
├── .env.example           # Root env template
├── README.md
├── TROUBLESHOOTING.md
└── LICENSE
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/models` | List available models |
| GET | `/api/sessions` | List all sessions |
| POST | `/api/sessions` | Create a new session |
| GET | `/api/sessions/:id` | Get session details |
| PATCH | `/api/sessions/:id/rename` | Rename a session |
| PATCH | `/api/sessions/:id/model` | Change session model |
| DELETE | `/api/sessions/:id` | Delete a session |
| GET | `/api/sessions/:id/messages` | Get session messages |
| WS | `/ws/debate/:id` | WebSocket for debate streaming |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | For OpenAI models | OpenAI API key |
| `ANTHROPIC_API_KEY` | For Claude models | Anthropic API key |
| `GEMINI_API_KEY` | For Gemini models | Google AI API key |
| `GROQ_API_KEY` | For Llama models | Groq API key |
| `MINIMAX_API_KEY` | For MiniMax models | MiniMax API key |
| `MINIMAX_GROUP_ID` | For MiniMax models | MiniMax group ID |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Built by Evan Lu
