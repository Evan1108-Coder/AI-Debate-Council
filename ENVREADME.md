# Environment Variables

This document explains every environment variable used by AI Debate Council. For installation steps, see [SETUP.md](SETUP.md).

## How Environment Files Work

The backend loads environment variables in this order:

1. **Shell environment** (any variables already set in your terminal).
2. **Root `.env`** (`<project-root>/.env`) — loaded with `override=True`, so it replaces shell values.
3. **Backend `.env`** (`<project-root>/backend/.env`) — loaded with `override=True`, so it replaces both shell and root values.

This means the `.env` files always win over shell-level variables. This is intentional: it prevents a stale API key in your shell from silently unlocking a provider you left blank in `.env`.

**For most setups, you only need one `.env` file at the project root.** The `backend/.env` exists for cases where you want backend-specific overrides.

## Quick Setup

```bash
cp .env.example .env
```

Then edit `.env` and add at least one provider API key for real debates.

## The Golden Rule

**Do not put model names in `.env`.** The app already knows every supported model through `MODEL_MAP` in `backend/app/model_registry.py`. It checks which provider API keys are present and enables those provider's models automatically.

Think of provider API keys as keys that unlock doors:

- `OPENAI_API_KEY` unlocks all 4 OpenAI models.
- `ANTHROPIC_API_KEY` unlocks all 4 Anthropic models.
- `GROQ_API_KEY` unlocks all 3 Llama models served through Groq.
- And so on for Google, MiniMax, and Moonshot.

The frontend calls `GET /api/models` and uses the returned `models` array for all dropdowns. That array contains only unlocked models. Each chat stores an Overall Model, and Chat Settings can optionally override the model for individual agent roles.

## Backend Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DATABASE_PATH` | No | `backend/data/debate_council.db` | Path to the SQLite database file. Relative paths resolve from the project root. The backend creates the directory and file automatically if they do not exist. |
| `FRONTEND_ORIGIN` | No | `http://localhost:6001` | Convenience origin for CORS when `CORS_ORIGINS` is not set. |
| `CORS_ORIGINS` | No | `http://localhost:6001` | Comma-separated list of frontend origins allowed to call the backend. The backend automatically adds both `localhost` and `127.0.0.1` variants. |
| `ALLOW_LOCALHOST_PORTS` | No | `false` | Set to `true` only for local development when you want to allow browser requests from any localhost or 127.0.0.1 port. Keep it `false` for sharing or production-like testing. |
| `DEBATE_ROUNDS` | No | `2` | Default number of debate rounds before the judge summary. Each round consists of one turn per active debater. With 3 debaters per team (6 total agents), 2 rounds means 12 debater turns. Users can override this per chat in Chat Settings (1–6). |
| `LITELLM_TIMEOUT_SECONDS` | No | `120` | Timeout in seconds for each model call through LiteLLM. Applies to both streamed debate turns and non-streamed moderator/classifier calls (capped at 30 seconds for those). |
| `MOCK_LLM_RESPONSES` | No | `false` | Set to `true` to stream local fake responses without any API keys. Useful for UI development and testing. When enabled and no real provider keys are set, a `mock-debate-model` appears in the dropdown. |

### Notes on CORS

The backend is intentionally narrow with CORS by default:

- `CORS_ORIGINS` and `FRONTEND_ORIGIN` values are used as explicit allowed origins.
- For each origin containing `localhost`, a `127.0.0.1` variant is added, and vice versa.
- `http://localhost:6001` and `http://127.0.0.1:6001` are always included.
- If `ALLOW_LOCALHOST_PORTS=true`, the regex pattern `http://(localhost|127\.0\.0\.1):[0-9]+` allows any localhost port as a development fallback.

For production, set `CORS_ORIGINS` to your actual frontend domain(s).

## Provider API Keys

Each key unlocks all models from that provider. You need at least one for real debates.

### OpenAI

```text
OPENAI_API_KEY=sk-...
```

**Models unlocked**: `gpt-5.4-pro`, `gpt-5.4-mini`, `gpt-4o`, `gpt-4o-mini`

Get your key from: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Anthropic

```text
ANTHROPIC_API_KEY=sk-ant-...
```

**Models unlocked**: `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-3.5-sonnet`

Get your key from: [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

### Google

```text
GOOGLE_API_KEY=AI...
```

**Models unlocked**: `gemini-3.1-pro`, `gemini-3-flash`, `gemini-2.5-flash-lite`

Get your key from: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### Groq (Llama Models)

```text
GROQ_API_KEY=gsk_...
```

**Models unlocked**: `llama-4-maverick`, `llama-4-scout`, `llama-3.3-70b`

Get your key from: [console.groq.com/keys](https://console.groq.com/keys)

### MiniMax

```text
MINIMAX_API_KEY=...
```

**Models unlocked**: `minimax-m2.7`, `minimax-m2.5-lightning`

### Moonshot

```text
MOONSHOT_API_KEY=...
```

**Models unlocked**: `kimi-latest`, `kimi-k2-thinking`, `kimi-k2-turbo-preview`, `kimi-k2.5-vision`, `moonshot-v1-128k`

### Placeholder Detection

The backend automatically ignores placeholder values. If your key is set to any of these, the provider will not activate:

`your_key_here`, `your_openai_key`, `your_anthropic_key`, `your_google_key`, `your_groq_key`, `your_minimax_key`, `your_moonshot_key`, `changeme`, `change_me`, `none`, `null`, `false`

### Verifying Key Detection

After starting the backend, open:

```text
http://localhost:8000/api/models
```

The response shows:

- `models`: Array of unlocked models (used by the frontend dropdown).
- `providers`: Array with each provider's configuration status and unlocked model count.
- `available_model_count`: Total number of unlocked models.
- `mock_mode`: Whether mock mode is active.

Example response with only OpenAI configured:

```json
{
  "models": [
    {"name": "gpt-5.4-pro", "provider": "openai", "provider_label": "OpenAI", "configured": true},
    {"name": "gpt-5.4-mini", "provider": "openai", "provider_label": "OpenAI", "configured": true},
    {"name": "gpt-4o", "provider": "openai", "provider_label": "OpenAI", "configured": true},
    {"name": "gpt-4o-mini", "provider": "openai", "provider_label": "OpenAI", "configured": true}
  ],
  "available_model_count": 4,
  "real_available_model_count": 4,
  "mock_mode": false
}
```

## Frontend Variables

The frontend works without extra environment variables when the backend runs on port 8000.

Create `frontend/.env.local` only if you need custom URLs:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | HTTP API base URL used by the browser. |
| `NEXT_PUBLIC_WS_URL` | No | Derived from `NEXT_PUBLIC_API_URL` | WebSocket base URL. If not set, the frontend replaces `http` with `ws` in the API URL. |

Because these variables start with `NEXT_PUBLIC_`, they are visible in browser JavaScript. **Never put secret API keys in frontend environment files.**

### Example: Backend on a Different Port

If the backend runs on port 8001, create `frontend/.env.local`:

```text
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

Restart the frontend dev server after changing `.env.local`.

## Complete .env Example

```text
# Backend
DATABASE_PATH=backend/data/debate_council.db
FRONTEND_ORIGIN=http://localhost:6001
CORS_ORIGINS=http://localhost:6001
ALLOW_LOCALHOST_PORTS=false
DEBATE_ROUNDS=2
LITELLM_TIMEOUT_SECONDS=120
MOCK_LLM_RESPONSES=false

# Provider API keys (add at least one for real debates)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
GROQ_API_KEY=
MINIMAX_API_KEY=
MOONSHOT_API_KEY=
```
