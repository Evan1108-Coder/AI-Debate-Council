# Troubleshooting

## Python Version Issues

Check your Python version:

```bash
python --version
python3.13 --version
```

The backend is designed for Python 3.13. If `python3.13` is not found, install Python 3.13 and recreate the virtual environment:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Virtual Environment Is Not Active

If imports fail after installation, make sure the virtual environment is active.

macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` in your terminal prompt.

## Missing Python Modules

Error examples:

```text
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'litellm'
```

Fix:

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

## Uvicorn Import Errors

Run the backend from the project root:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

If you run the command from inside `backend/`, Python may not resolve the package the same way.

## Port 8000 Is Already In Use

Start the backend on another port:

```bash
uvicorn backend.app.main:app --reload --port 8001
```

Then create `frontend/.env.local`:

```text
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

Restart the frontend after changing frontend environment variables.

## Port 6001 Is Already In Use

Next.js may offer another port automatically. You can also choose one:

```bash
cd frontend
npm run dev -- -p 6001
```

If the frontend origin changes, update `.env`:

```text
CORS_ORIGINS=http://localhost:6001
FRONTEND_ORIGIN=http://localhost:6001
```

Restart the backend.

## API Keys Are Not Detected

Open:

```text
http://localhost:8000/api/models
```

If a provider says it is not configured:

- Confirm `.env` exists at the project root or `backend/.env`.
- Confirm the key name is exact, such as `OPENAI_API_KEY`.
- Restart the backend after editing `.env`.
- Do not put quotes around the key unless they are part of the key.
- Do not put model names in `.env`.

## No Models Appear In The Dropdown

`GET /api/models` returns only unlocked models in the `models` array. Add at least one provider key for real debates.

Examples:

- `OPENAI_API_KEY` alone unlocks 4 OpenAI models.
- `ANTHROPIC_API_KEY` alone unlocks 4 Anthropic models.
- `OPENAI_API_KEY` plus `ANTHROPIC_API_KEY` unlocks 8 models.
- All 6 provider keys unlock all 21 models.

If no provider keys are set, the real model dropdown is empty and debates cannot start.

## "Choose One Unlocked Model"

The user must select one Overall Model from the dropdown before sending a message. By default, Pro and Con team agents, the Council Assistant, the optional Judge Assistant, and the Judge use that model. In Chat Settings, each chat can override model, temperature, max tokens, and response length per agent role.

For UI testing without real APIs:

```text
MOCK_LLM_RESPONSES=true
```

Restart the backend.

## LiteLLM Provider Errors

Errors from model providers can look like authentication failures, quota errors, model-not-found errors, or rate limits.

Check:

- The API key is valid and has quota.
- The provider account has access to the requested model.
- The model name in `backend/app/model_registry.py` matches the provider and LiteLLM route.
- Your network can reach the provider API.

## CORS Errors

Browser console examples:

```text
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:6001' has been blocked by CORS policy
```

Fix `.env`:

```text
CORS_ORIGINS=http://localhost:6001
FRONTEND_ORIGIN=http://localhost:6001
```

For multiple origins:

```text
CORS_ORIGINS=http://localhost:6001,http://127.0.0.1:6001
```

Restart the backend.

## WebSocket Connection Failed

Check:

- Backend is running.
- Frontend `NEXT_PUBLIC_WS_URL` points to the backend WebSocket origin.
- Browser can reach `ws://localhost:8000/ws/debates/{session_id}`.
- Reverse proxies are configured to allow WebSocket upgrades.

If the backend port changed to `8001`, set:

```text
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

## SQLite Database Issues

Default database path:

```text
backend/data/debate_council.db
```

If the database folder is missing, the backend creates it automatically.

If you want a fresh local database, stop the backend and delete the database files:

```bash
rm -f backend/data/debate_council.db backend/data/debate_council.db-shm backend/data/debate_council.db-wal
```

On Windows PowerShell:

```powershell
Remove-Item backend\data\debate_council.db* -ErrorAction SilentlyContinue
```

Then restart the backend.

## Session Limit

The app allows 10 sessions at a time. If you get a limit error, delete a session before creating another.

Session numbers are not reused while any session still exists. If all sessions are deleted, the next created session is `Debate Session #1`.

## Active Debate Limit

The backend allows 3 active debates at the same time. If a fourth starts, the backend returns an error. Wait for one debate to finish and try again.

This limit is process-local. In production, use a single worker or move active-debate tracking to shared storage such as Redis.

## Node or npm Issues

Check versions:

```bash
node --version
npm --version
```

Use Node.js 20 or newer. Then reinstall frontend dependencies:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

On Windows PowerShell:

```powershell
cd frontend
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item package-lock.json -ErrorAction SilentlyContinue
npm install
```

## Frontend Build Errors

Run:

```bash
cd frontend
npm run build
```

Common fixes:

- Run `npm install`.
- Delete `frontend/.next` and build again.
- Confirm `frontend/tsconfig.json` includes the `@/*` path alias.
- Restart the dev server after changing `.env.local`.

## Tailwind Styles Do Not Load

Check these files exist:

- `frontend/app/globals.css`
- `frontend/tailwind.config.ts`
- `frontend/postcss.config.mjs`

Restart the frontend dev server.

## Windows PowerShell Blocks Activation

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

## macOS `python3.13` Not Found

If Homebrew installed Python but the command is missing:

```bash
brew info python@3.13
```

Follow the PATH instructions shown by Homebrew, then open a new terminal.

## Backend Starts But Frontend Shows No Sessions

Check:

- `http://localhost:8000/health` returns `{"status":"ok"}`.
- Browser devtools Network tab can reach `/api/sessions`.
- `CORS_ORIGINS` includes the frontend origin.
- The backend terminal does not show database permission errors.

## Real Providers Are Slow

The debate uses multiple streamed model calls. You can reduce turns:

```text
DEBATE_ROUNDS=1
```

Restart the backend.
