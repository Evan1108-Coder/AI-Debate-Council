# Troubleshooting

Solutions for every known issue with AI Debate Council. For installation steps, see [SETUP.md](SETUP.md). For environment variable details, see [ENVREADME.md](ENVREADME.md).

## Table of Contents

- [Python Issues](#python-issues)
- [Virtual Environment Issues](#virtual-environment-issues)
- [Backend Startup Issues](#backend-startup-issues)
- [Port Conflicts](#port-conflicts)
- [API Key and Model Issues](#api-key-and-model-issues)
- [CORS Issues](#cors-issues)
- [WebSocket Issues](#websocket-issues)
- [Database Issues](#database-issues)
- [Frontend Issues](#frontend-issues)
- [Debate and Chat Issues](#debate-and-chat-issues)
- [Provider-Specific Issues](#provider-specific-issues)
- [Performance Issues](#performance-issues)
- [Windows-Specific Issues](#windows-specific-issues)
- [macOS-Specific Issues](#macos-specific-issues)

---

## Python Issues

### Python 3.13 Not Found

Check your Python version:

```bash
python --version
python3 --version
python3.13 --version
```

The backend requires Python 3.13. If `python3.13` is not found:

**macOS with Homebrew:**

```bash
brew install python@3.13
```

If Homebrew installed Python but the command is not found:

```bash
brew info python@3.13
```

Follow the PATH instructions shown by Homebrew, then open a new terminal.

**Windows:**

Download from [python.org/downloads](https://www.python.org/downloads/). Make sure to check "Add Python to PATH" during installation.

```powershell
py -3.13 --version
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install python3.13 python3.13-venv
```

### Wrong Python Version in Virtual Environment

If you created the virtual environment with the wrong Python version:

```bash
rm -rf .venv
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

On Windows:

```powershell
Remove-Item .venv -Recurse -Force
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

## Virtual Environment Issues

### Virtual Environment Is Not Active

If imports fail after installation, the virtual environment is probably not active.

**macOS/Linux:**

```bash
source .venv/bin/activate
```

**Windows:**

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the beginning of your terminal prompt. If you do not see it, the environment is not active.

### Missing Python Modules

Error examples:

```text
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'litellm'
ModuleNotFoundError: No module named 'dotenv'
ModuleNotFoundError: No module named 'uvicorn'
```

Fix:

1. Activate the virtual environment.
2. Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### PowerShell Blocks Activation (Windows)

Error:

```text
.\.venv\Scripts\Activate.ps1 : File ... cannot be loaded because running scripts is disabled on this system.
```

Fix:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Backend Startup Issues

### Uvicorn Import Error

Always run the backend from the **project root**, not from inside `backend/`:

```bash
# Correct on macOS/Linux, from project root
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# Wrong (from inside backend/)
cd backend
uvicorn app.main:app --reload --port 8000   # This may fail
```

On Windows PowerShell, use:

```powershell
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### `uvicorn: command not found`

This usually means Uvicorn is installed inside the project's virtual environment, but your shell PATH is not currently pointing at that environment. Start the backend with the venv Python module command instead:

```bash
cd "/Users/EvanLu/AI Debate Council - MultiAI System - CodeX"
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

You can also activate the virtual environment first and then use `python -m uvicorn ...`, but the explicit `.venv/bin/python -m uvicorn ...` command is the safest copy-paste version.

If you get `ModuleNotFoundError: No module named 'backend'`, you are not in the project root.

### "No module named 'backend.app'"

This means Python cannot find the backend package. Check:

1. You are in the project root directory (the folder containing `backend/`, `frontend/`, `.env.example`).
2. The virtual environment is active.
3. The `backend/app/__init__.py` file exists.

### Backend Starts but Immediately Crashes

Check the terminal output for error messages. Common causes:

- Missing dependencies: Run `pip install -r backend/requirements.txt`.
- Invalid `.env` syntax: Make sure there are no stray quotes or spaces around `=` signs.
- Database permission error: The backend needs write access to the `backend/data/` directory.

### Backend Starts but Returns 500 Errors

Check the uvicorn terminal for traceback details. Common causes:

- Database is locked by another process.
- Corrupted database file. See [Database Issues](#database-issues).

## Port Conflicts

### Port 8000 Is Already in Use

Error:

```text
ERROR:    [Errno 48] error while attempting to bind on address ('127.0.0.1', 8000): address already in use
```

**Option 1**: Kill the process using port 8000:

```bash
# macOS/Linux
lsof -ti:8000 | xargs kill

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Option 2**: Use a different port:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8001
```

Then create `frontend/.env.local`:

```text
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

Restart the frontend.

### Port 6001 Is Already in Use

Next.js may automatically offer another port. You can also specify one:

```bash
cd frontend
npm run dev -- -p 6002
```

If the frontend port changes, update `.env`:

```text
CORS_ORIGINS=http://localhost:6002
FRONTEND_ORIGIN=http://localhost:6002
```

Restart the backend.

## API Key and Model Issues

### No Models Appear in the Dropdown

The model dropdown shows only unlocked models. If it is empty:

1. Open `http://localhost:8000/api/models` to check which providers are configured.
2. Make sure `.env` exists at the project root (or `backend/.env`).
3. Make sure the API key variable name is exact (e.g., `OPENAI_API_KEY`, not `OPENAI_KEY`).
4. Make sure the key value is not a placeholder like `your_key_here`, `changeme`, `none`, or `false`.
5. Restart the backend after editing `.env`.
6. Do not put quotes around the key unless they are part of the key itself.

Key-to-model mapping:

| API Key Variable | Models Unlocked |
| --- | --- |
| `OPENAI_API_KEY` | `gpt-5.4-pro`, `gpt-5.4-mini`, `gpt-4o`, `gpt-4o-mini` |
| `ANTHROPIC_API_KEY` | `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-3.5-sonnet` |
| `GOOGLE_API_KEY` | `gemini-3.1-pro`, `gemini-3-flash`, `gemini-2.5-flash-lite` |
| `GROQ_API_KEY` | `llama-4-maverick`, `llama-4-scout`, `llama-3.3-70b` |
| `MINIMAX_API_KEY` | `minimax-m2.7`, `minimax-m2.5-lightning` |
| `MOONSHOT_API_KEY` | `kimi-latest`, `kimi-k2-thinking`, `kimi-k2-turbo-preview`, `kimi-k2.5-vision`, `moonshot-v1-128k` |

### "Choose One Unlocked Model"

This error means the user has not selected an Overall Model from the dropdown. Select a model before sending a message.

If the dropdown is empty, see [No Models Appear in the Dropdown](#no-models-appear-in-the-dropdown).

For testing without real APIs, set `MOCK_LLM_RESPONSES=true` in `.env` and restart the backend.

### API Key Is Set but Provider Shows "Not Configured"

1. Open `http://localhost:8000/api/models`.
2. Check the `providers` array for your provider's `configured` field.
3. If `configured` is `false`:
   - The key variable name may be wrong. It must be exactly `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `MINIMAX_API_KEY`, or `MOONSHOT_API_KEY`.
   - The key value may be a placeholder. See the placeholder list in [ENVREADME.md](ENVREADME.md).
   - There may be extra spaces or invisible characters in the key. Copy-paste the key fresh.
   - The `.env` file may not be in the right location. It should be at the project root or `backend/.env`.
4. Restart the backend after any `.env` changes.

### Shell Environment Variable Overriding .env

The backend loads `.env` files with `override=True`, which means `.env` values replace shell variables. If you still see unexpected behavior:

1. Check for a `backend/.env` file that might be overriding your root `.env`.
2. Unset the shell variable: `unset OPENAI_API_KEY` (macOS/Linux) or `$env:OPENAI_API_KEY = ""` (PowerShell).

## CORS Issues

### Browser Console Shows CORS Errors

Error example:

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
CORS_ORIGINS=http://localhost:6001,http://localhost:3000
```

Restart the backend.

The backend automatically adds `localhost` and `127.0.0.1` variants for each origin, plus a regex matching any localhost port. Most CORS issues come from forgetting to restart the backend after changing `.env`.

### CORS Error After Changing Frontend Port

If the frontend is running on a port other than 6001:

1. Update `.env`:

   ```text
   CORS_ORIGINS=http://localhost:YOUR_PORT
   FRONTEND_ORIGIN=http://localhost:YOUR_PORT
   ```

2. Restart the backend.

## WebSocket Issues

### WebSocket Connection Failed

Symptoms: The frontend shows "Backend is not reachable" or debates never start streaming.

Check:

1. The backend is running: Open `http://localhost:8000/health`.
2. The frontend knows the correct WebSocket URL. Default is `ws://localhost:8000`. If the backend is on a different port, create `frontend/.env.local`:

   ```text
   NEXT_PUBLIC_WS_URL=ws://localhost:8001
   ```

3. No firewall is blocking WebSocket connections.
4. If using a reverse proxy (nginx, etc.), it must be configured to allow WebSocket upgrades:

   ```nginx
   location /ws/ {
       proxy_pass http://localhost:8000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```

### WebSocket Disconnects Mid-Debate

This can happen if:

- The backend crashes (check the uvicorn terminal for errors).
- The LiteLLM request times out. Increase `LITELLM_TIMEOUT_SECONDS` in `.env`:

  ```text
  LITELLM_TIMEOUT_SECONDS=180
  ```

- The browser tab was inactive too long and the OS throttled the connection.
- A network proxy or VPN dropped the long-running connection.

### "Session not found" on WebSocket Connect

The WebSocket URL includes a session ID: `ws://localhost:8000/ws/debates/{session_id}`. This error means the session was deleted while the frontend was still connected. Create a new session.

## Database Issues

### Database File Not Found

The backend creates the database directory and file automatically on startup. If you see a path error:

1. Check `DATABASE_PATH` in `.env`. Default is `backend/data/debate_council.db`.
2. Make sure the backend has write permissions to the parent directory.
3. If using an absolute path, make sure all parent directories exist.

### Database Is Locked

Error:

```text
sqlite3.OperationalError: database is locked
```

This means another process has the database open. Common causes:

- Two backend instances running at the same time.
- A database browser tool (DB Browser for SQLite, etc.) has the file open.

Fix: Stop the other process and restart the backend.

### Corrupted Database

If you see database errors that persist:

1. Stop the backend.
2. Delete the database files:

   ```bash
   rm -f backend/data/debate_council.db backend/data/debate_council.db-shm backend/data/debate_council.db-wal
   ```

   On Windows:

   ```powershell
   Remove-Item backend\data\debate_council.db* -ErrorAction SilentlyContinue
   ```

3. Restart the backend. A fresh database will be created automatically.

This deletes all sessions, debates, and messages.

### Fresh Database

To start over with a clean database without deleting the project:

```bash
rm -f backend/data/debate_council.db*
```

Restart the backend.

## Frontend Issues

### Node.js or npm Version Issues

Check versions:

```bash
node --version   # Should be 20+
npm --version    # Should be 10+
```

If outdated, install the latest LTS from [nodejs.org](https://nodejs.org/).

### npm install Fails

Try a clean install:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

On Windows:

```powershell
cd frontend
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item package-lock.json -ErrorAction SilentlyContinue
npm install
```

### Frontend Build Errors

```bash
cd frontend
npm run build
```

Common fixes:

- Run `npm install` first.
- Delete `frontend/.next` and build again:

  ```bash
  rm -rf frontend/.next
  cd frontend
  npm run build
  ```

- Confirm `frontend/tsconfig.json` includes the `@/*` path alias.
- Restart the dev server after changing `.env.local`.

### Tailwind Styles Do Not Load

Check that these files exist:

- `frontend/app/globals.css`
- `frontend/tailwind.config.ts`
- `frontend/postcss.config.mjs`

If they exist, restart the frontend dev server.

### Frontend Shows "Backend is not reachable"

1. Check that the backend is running: Open `http://localhost:8000/health`.
2. Check that the frontend is using the correct API URL. Default is `http://localhost:8000`. If different, set `NEXT_PUBLIC_API_URL` in `frontend/.env.local`.
3. Check browser devtools Network tab for failed requests.
4. Check that CORS is configured (see [CORS Issues](#cors-issues)).

### Frontend Shows No Sessions After Login

1. Verify `http://localhost:8000/health` returns `{"status":"ok"}`.
2. Check browser devtools Network tab — `GET /api/sessions` should return 200.
3. Check CORS (see [CORS Issues](#cors-issues)).
4. Check the backend terminal for database permission errors.

## Debate and Chat Issues

### Debate Never Starts

1. Make sure a model is selected in the Overall Model dropdown.
2. Make sure the message is not empty.
3. Check the browser devtools Console for WebSocket errors.
4. Check the backend terminal for error messages.

### "This chat is already working"

This means a debate or chat is already running in this session. Wait for it to finish, or create a new session.

### "Only 3 debates can run at the same time"

The backend limits concurrent debates to 3 across all sessions. Wait for one to finish and try again.

This limit is process-local. In production with multiple workers, move active-debate tracking to shared storage like Redis.

### Session Limit (10 Sessions)

The app allows 10 sessions at a time. If you get a 409 error, delete a session before creating a new one.

Session numbers are monotonic — deleted numbers are never reused while any session exists. If all sessions are deleted, the counter resets and the next session is `Debate Session #1`.

### Intent Classifier Sends Chat to Debate (or Vice Versa)

The system uses an LLM-based intent classifier with a heuristic fallback. If it misclassifies:

- To force chat mode: Enable "Always On" for the Council Assistant in Chat Settings.
- To force debate mode: Start your message with "debate" or "let them debate" — these are explicit debate markers.
- Heuristic markers for chat: "hello", "hi", "thanks", "explain", "summarize", "how do i".
- Heuristic markers for debate: "debate", "argue both sides", "pro and con", "pros and cons", "should", "vs", "which is better".

### Agent Uses Wrong Model

Each agent role defaults to the session's Overall Model. To override for a specific role:

1. Go to Chat Settings.
2. Under "Shared team roles" or "Neutral roles", find the agent.
3. Set a specific model in its Model dropdown.

Note: Team role settings apply to both Pro and Con versions of that role.

### Debate Turns Seem Repetitive

Try:

- Reducing debate rounds in Chat Settings (1–2 rounds usually suffice).
- Setting debaters per team to 2 or 3 (4 debaters with many rounds can get repetitive).
- The moderator LLM can signal "END" to stop early if it detects repetition, but this requires a real (non-mock) model.

### Response Gets Truncated

If a message ends with "_Response reached the max-token limit..._":

1. Go to Chat Settings.
2. Find the agent role whose response was truncated.
3. Increase its Max tokens value (up to 2000).

The system automatically attempts one continuation when a response is truncated, but very long responses may still hit the combined limit.

### Clear History vs Clear Memory

- **Clear Chat History**: Hides visible messages and debate statistics. The hidden messages are still available as memory for follow-up Council Assistant responses. Useful for cleaning up the UI while preserving context.
- **Clear Chat Memory**: Permanently deletes all messages and debates for the session. The session itself remains but has no history. Use this for a true fresh start within the same session.

## Provider-Specific Issues

### LiteLLM Provider Errors

Errors from model providers appear as messages like:

```text
claude-sonnet-4-6 failed through LiteLLM: ...
```

Common causes:

- **Authentication error**: The API key is invalid or expired. Get a new key from the provider.
- **Quota/billing error**: Your account has run out of credits. Check your provider dashboard.
- **Rate limit**: You are sending too many requests. Wait and retry, or use a different model.
- **Model not found**: The model name in `MODEL_MAP` does not match what the provider expects. This should not happen with the built-in model list, but could occur if the registry was modified.
- **Network error**: Your machine cannot reach the provider API. Check your internet connection.

### OpenAI Errors

- `401 Unauthorized`: Invalid API key.
- `429 Rate limit`: Too many requests. Wait 30 seconds and retry.
- `500/503 Server error`: OpenAI is experiencing issues. Try again later or switch to another provider.

### Anthropic Errors

- `401 Authentication error`: Invalid API key.
- `429 Rate limit`: Too many requests. Anthropic has per-minute and per-day limits.
- `529 Overloaded`: Anthropic servers are busy. The backend retries up to 3 times automatically.

### Google Gemini Errors

- `400 Invalid API key`: Check that `GOOGLE_API_KEY` is a valid Gemini/AI Studio key.
- `403 Permission denied`: Your Google Cloud project may not have the Gemini API enabled.

### Groq Errors

- `401 Invalid API key`: Check `GROQ_API_KEY`.
- `429 Rate limit`: Groq has aggressive rate limits on free tier. Wait or upgrade.
- `413 Request too large`: Reduce max tokens or context window.

### MiniMax and Moonshot Errors

These providers may have different error formats. Check:

- The API key is valid.
- Your account has credits.
- The provider service is not down.

## Performance Issues

### Debates Are Slow

The debate uses multiple streamed model calls sequentially. Each turn waits for the previous one to finish. To speed things up:

- **Reduce debate rounds**: Set `DEBATE_ROUNDS=1` in `.env` or change it per chat in Chat Settings.
- **Reduce debaters per team**: 2 debaters × 1 round = 4 turns + judge. 4 debaters × 3 rounds = 24 turns + judge assistant + judge.
- **Use faster models**: `gpt-4o-mini`, `claude-haiku-4-5`, `gemini-2.5-flash-lite`, and `llama-3.3-70b` are generally faster than their larger counterparts.
- **Use Groq**: Groq's inference is very fast for Llama models.
- **Increase timeout**: If turns are timing out, increase `LITELLM_TIMEOUT_SECONDS` in `.env`.

### Analytics Are Slow

The analytics engine is lightweight (pure Python, no ML dependencies) and processes after each turn. If the debate has many turns with long content, analytics may take a moment. This is normal and does not block streaming.

### High Memory Usage

SQLite keeps the database in memory while connections are open. For very large databases with thousands of debates:

- Delete old sessions you no longer need.
- Or reset the database: `rm -f backend/data/debate_council.db*` and restart.

## Windows-Specific Issues

### `python` Command Not Found

On Windows, use `py -3.13` instead of `python3.13`:

```powershell
py -3.13 -m venv .venv
```

### Path Too Long Errors

Windows has a 260-character path limit. If `npm install` fails with path errors:

1. Clone the repo to a shorter path (e.g., `C:\Projects\AI-Debate-Council`).
2. Or enable long paths in Windows:

   ```powershell
   # Run as Administrator
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

### Line Ending Issues

If the backend crashes with syntax errors after cloning on Windows:

```bash
git config core.autocrlf input
git checkout -- .
```

### Antivirus Blocks Python/Node

Some antivirus software blocks Python or Node.js processes. If the backend or frontend fails to start:

1. Check your antivirus logs.
2. Add exceptions for `python.exe`, `node.exe`, and the project directory.

## macOS-Specific Issues

### `python3.13` Not Found After Homebrew Install

```bash
brew info python@3.13
```

Follow the PATH instructions shown. You may need to add to your `~/.zshrc`:

```bash
export PATH="/opt/homebrew/opt/python@3.13/bin:$PATH"
```

Then:

```bash
source ~/.zshrc
```

### Xcode Command Line Tools Required

If `pip install` fails with compilation errors:

```bash
xcode-select --install
```

### macOS Firewall Prompt

When starting the backend, macOS may ask to allow incoming network connections. Click "Allow" for the debates to work in the browser.
