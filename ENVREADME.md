# Environment Variables Guide

This document explains every environment variable used by AI Debate Council.

## Quick Start

You only need API keys for the providers you want to use. For example, to use just GPT models, only `OPENAI_API_KEY` is required.

## Backend Variables (`backend/.env`)

### API Keys

| Variable | Required? | Description | How to Get It |
|----------|-----------|-------------|---------------|
| `OPENAI_API_KEY` | For OpenAI models | API key for GPT models (gpt-5.4-pro, gpt-5.4-mini, gpt-4o, gpt-4o-mini) | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | For Anthropic models | API key for Claude models (claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5, claude-3.5-sonnet) | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |
| `GEMINI_API_KEY` | For Google models | API key for Gemini models (gemini-3.1-pro, gemini-3-flash, gemini-2.5-flash-lite) | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `GROQ_API_KEY` | For Llama models | API key for Llama models via Groq (llama-4-maverick, llama-4-scout, llama-3.3-70b) | [console.groq.com/keys](https://console.groq.com/keys) |
| `MINIMAX_API_KEY` | For MiniMax models | API key for MiniMax models (minimax-m2.7, minimax-m2.5-lightning) | [platform.minimaxi.com](https://platform.minimaxi.com/) |
| `MOONSHOT_API_KEY` | For Moonshot/Kimi models | API key for Kimi models (kimi-latest, kimi-k2-thinking, kimi-k2-turbo-preview, kimi-k2.5-vision, moonshot-v1-128k) | [platform.moonshot.cn](https://platform.moonshot.cn/) |

### Server Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address for the backend server |
| `PORT` | `8000` | Port for the backend server |

## Frontend Variables (`frontend/.env.local`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL of the backend API. Change this if the backend runs on a different host or port. |

## Which Keys Do I Need?

It depends on which models you want to use in debates:

| If you want to use... | You need... |
|------------------------|-------------|
| GPT-5.4-pro, GPT-5.4-mini, GPT-4o, GPT-4o-mini | `OPENAI_API_KEY` |
| Claude Opus 4.6, Sonnet 4.6, Haiku 4.5, Claude 3.5 Sonnet | `ANTHROPIC_API_KEY` |
| Gemini 3.1 Pro, Gemini 3 Flash, Gemini 2.5 Flash Lite | `GEMINI_API_KEY` |
| Llama 4 Maverick, Llama 4 Scout, Llama 3.3 70B | `GROQ_API_KEY` |
| MiniMax M2.7, MiniMax M2.5 Lightning | `MINIMAX_API_KEY` |
| Kimi Latest, Kimi K2 Thinking, Kimi K2 Turbo Preview, Kimi K2.5 Vision, Moonshot V1 128K | `MOONSHOT_API_KEY` |

**Minimum requirement:** At least one API key from any provider above.

## Example `.env` File

```env
# I only use OpenAI and Anthropic models
OPENAI_API_KEY=sk-proj-abc123...
ANTHROPIC_API_KEY=sk-ant-abc123...

# Leave others empty or remove them
GEMINI_API_KEY=
GROQ_API_KEY=
MINIMAX_API_KEY=
MOONSHOT_API_KEY=

# Server (defaults are fine for local development)
HOST=0.0.0.0
PORT=8000
```

## Notes

- API keys are **never** sent to the frontend. They stay on the backend server only.
- If you select a model in the UI but don't have the corresponding API key configured, the debate will show an error message for that debater's turn.
- LiteLLM handles all provider-specific API formatting automatically. You just provide the keys.
- Keep your `.env` file private. It is already in `.gitignore` and will not be committed to the repository.
