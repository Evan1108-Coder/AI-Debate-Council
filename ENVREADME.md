# Environment Variables

Copy `.env.example` to `.env` at the project root. The root `.env` is the normal local development file.

Do not put model names in any `.env` file. The app already knows the supported model list through `MODEL_MAP` in `backend/app/model_registry.py`. It checks which provider API keys are present and enables those provider models automatically.

Think of provider API keys as keys that unlock doors:

- `OPENAI_API_KEY` unlocks all OpenAI models.
- `ANTHROPIC_API_KEY` unlocks all Anthropic models.
- `GROQ_API_KEY` unlocks all Llama models served through Groq.

The frontend calls `GET /api/models` and uses the returned `models` array for the dropdown. That array contains only unlocked models. Each chat stores an Overall Model, and Chat Settings can optionally override the model for individual roles.

## Backend Variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DATABASE_PATH` | No | `backend/data/debate_council.db` | SQLite database file path. Relative paths resolve from the project root. |
| `FRONTEND_ORIGIN` | No | `http://localhost:6001` | Convenience origin for CORS when `CORS_ORIGINS` is not set. |
| `CORS_ORIGINS` | No | `http://localhost:6001` | Comma-separated list of frontend origins allowed to call the backend. |
| `DEBATE_ROUNDS` | No | `2` | Number of debate rounds before the judge summary. |
| `LITELLM_TIMEOUT_SECONDS` | No | `120` | Timeout for each model call through LiteLLM. |
| `MOCK_LLM_RESPONSES` | No | `false` | Set to `true` to stream local fake responses without API keys. |

## Provider API Keys

| Variable | Provider | Models enabled |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI | `gpt-5.4-pro`, `gpt-5.4-mini`, `gpt-4o`, `gpt-4o-mini` |
| `ANTHROPIC_API_KEY` | Anthropic | `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-3.5-sonnet` |
| `GOOGLE_API_KEY` | Google | `gemini-3.1-pro`, `gemini-3-flash`, `gemini-2.5-flash-lite` |
| `GROQ_API_KEY` | Groq | `llama-4-maverick`, `llama-4-scout`, `llama-3.3-70b` |
| `MINIMAX_API_KEY` | MiniMax | `minimax-m2.7`, `minimax-m2.5-lightning` |
| `MOONSHOT_API_KEY` | Moonshot | `kimi-latest`, `kimi-k2-thinking`, `kimi-k2-turbo-preview`, `kimi-k2.5-vision`, `moonshot-v1-128k` |

## Frontend Variables

The frontend works without extra environment variables when the backend runs on port `8000`.

Create `frontend/.env.local` only if you need custom URLs:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | HTTP API base URL used by the browser. |
| `NEXT_PUBLIC_WS_URL` | No | Derived from `NEXT_PUBLIC_API_URL` | WebSocket base URL used by the browser. |

Because these variables start with `NEXT_PUBLIC_`, they are visible in browser JavaScript. Never put secret API keys in frontend environment files.
