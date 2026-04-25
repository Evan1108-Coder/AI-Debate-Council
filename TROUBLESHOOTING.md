# Troubleshooting

Solutions for every known issue with AI Debate Council. For installation steps, see [SETUP.md](SETUP.md). For environment variable details, see [ENVREADME.md](ENVREADME.md).

## Table of Contents

- [First Launch Issues](#first-launch-issues)
- [macOS Gatekeeper Blocks the App](#macos-gatekeeper-blocks-the-app)
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
- [Desktop App (Electron) Issues](#desktop-app-electron-issues)

---

## First Launch Issues

### First Launch Takes a Long Time

The very first time you open the app after installing, it needs to download and install Python packages. This normally takes **1–3 minutes** depending on your internet speed. The splash screen shows which package is currently being installed.

If it takes longer than 5 minutes, your connection may be slow. This is not a bug — the app is downloading packages from the internet. Leave it running and it will finish.

### Pip Install Hangs (App Stuck on "Installing…") {#pip-install-hangs}

If the splash screen stays on "Installing Python packages…" or a specific package name for a very long time:

**Most common cause: slow or blocked internet connection.**

Try these fixes in order:

1. **Wait a bit longer.** Some packages (like `litellm` and its dependencies) are large. On a slow connection this can take 5–10 minutes.
2. **Disconnect VPN/proxy.** VPNs and corporate proxies often interfere with pip downloads. Disconnect your VPN, close the app, and try again.
3. **Check your internet.** Open a browser and load any website. If the browser is slow too, the issue is your network, not the app.
4. **Close and retry.** Close the splash screen (click the red button on macOS or × on Windows) and reopen the app. The app retries the installation automatically.
5. **Try a different network.** If you're on corporate/school WiFi, try your phone hotspot.

If it still fails after retrying, you can install the packages manually:

**macOS:**

```bash
cd ~/Library/Application\ Support/ai-debate-council/backend-env
source .venv/bin/activate
pip install --no-cache-dir --timeout 60 -r /Applications/AI\ Debate\ Council.app/Contents/Resources/app-content/backend/requirements.txt
```

**Windows (PowerShell):**

```powershell
cd "$env:APPDATA\ai-debate-council\backend-env"
.\.venv\Scripts\Activate.ps1
pip install --no-cache-dir --timeout 60 -r "$env:LOCALAPPDATA\Programs\ai-debate-council\resources\app-content\backend\requirements.txt"
```

Then relaunch the app — it will detect the installed packages and skip the install step.

### App Closes Immediately on Launch

This usually means Python is not installed or is too old. The app requires Python 3.10 or newer. Check:

```bash
python3 --version
```

If this shows a version below 3.10, or if the command is not found, install Python from [python.org/downloads](https://www.python.org/downloads/).

On macOS, if you installed Python via Homebrew but the app can't find it, try launching the app from Terminal:

```bash
open /Applications/AI\ Debate\ Council.app
```

This gives the app access to Homebrew's PATH.

---

## macOS Gatekeeper Blocks the App {#macos-gatekeeper-blocks-the-app}

macOS has a security feature called **Gatekeeper** that blocks apps not signed with an Apple Developer certificate. Since this is an open-source app, it is not code-signed, so macOS will try to block it the first time you open it. This section covers every Gatekeeper scenario.

### App Icon Bounces in Dock but Nothing Opens

This is the most common first-launch issue. You double-click or right-click → Open the app, the icon bounces in the Dock, but no window appears. Behind the scenes, macOS is running a Gatekeeper verification check.

**What to do:**

1. **Wait 10–30 seconds.** The verification usually finishes on its own and the app window will appear.
2. **Click the bouncing app icon in the Dock.** Sometimes the security dialog opens behind other windows — clicking the icon brings it to the front.
3. **If nothing happens after 1 minute**, open **System Settings** → **Privacy & Security**. Scroll down to the Security section. You will see a message saying "AI Debate Council was blocked." Click **Open Anyway**, enter your password, then click **Open**.

If this still does not work, run this command in Terminal to permanently remove the quarantine flag:

```bash
sudo xattr -cr /Applications/AI\ Debate\ Council.app
```

Then double-click the app normally. You only need to do this once.

### "正在验证" / "Verifying…" Spinner {#macos-verifying-dialog}

When you open the `.dmg` installer or the app for the first time, macOS shows a spinning progress bar with the text "正在验证…" (Chinese) or "Verifying…" (English).

**Normal behavior:** This takes 10–30 seconds and then disappears.

**If it takes longer than 1 minute:**

1. **Cancel it** (press `⌘ + .` or click Cancel if available)
2. Right-click the `.dmg` or app → **Open**
3. If a security dialog appears, click **Open**

**If it keeps happening every time you open the app:**

```bash
sudo xattr -cr /Applications/AI\ Debate\ Council.app
```

This removes the quarantine flag that triggers the verification. You only need to run this once.

### "AI Debate Council is Damaged and Can't Be Opened"

This does NOT mean the file is actually damaged. macOS shows this when Gatekeeper blocks an unsigned app. Fix:

```bash
sudo xattr -cr /Applications/AI\ Debate\ Council.app
```

Then double-click the app normally.

### "macOS Cannot Verify That This App Is Free From Malware"

This is normal for open-source apps. Two ways to open:

**Method 1 — Right-click (recommended for first time):**

1. Right-click (or Ctrl+click) the app in Finder → Applications
2. Click **Open** from the context menu
3. Click **Open** in the dialog that appears

**Method 2 — System Settings:**

1. Open **System Settings** → **Privacy & Security**
2. Scroll down — you will see "AI Debate Council was blocked from use"
3. Click **Open Anyway** → enter your password → click **Open**

You only need to do this once. macOS remembers your choice after the first approval.

### "你不能打开应用程序，因为它没有响应" / "Can't Open Because It Is Not Responding"

macOS shows this dialog when an app takes too long to display its first window. For AI Debate Council, this can happen because:

1. **Gatekeeper verification is still running in the background.** The app is waiting for macOS to finish the security check before it can show the splash screen.
2. **The app is setting up the Python environment.** On first launch, the app creates a Python virtual environment and installs packages — this happens before any window appears.

**What to do:**

1. **Click OK** to dismiss the dialog — do NOT force-quit the app yet.
2. **Wait 30–60 seconds.** The splash screen should appear once Gatekeeper finishes and the app starts loading.
3. **If nothing happens after 1 minute**, force-quit the app (right-click the Dock icon → Force Quit), then:
   - Remove the quarantine flag: `sudo xattr -cr /Applications/AI\ Debate\ Council.app`
   - Open the app again by right-clicking → Open in Finder

This dialog typically only appears on the very first launch. Subsequent launches are much faster.

### "xattr: Operation not permitted" (Even With sudo)

If you run `sudo xattr -cr /Applications/AI\ Debate\ Council.app` and still get "Operation not permitted", macOS is blocking Terminal from modifying app attributes. This is a macOS security feature called **System Integrity Protection (SIP)**.

**Fix — Grant Terminal Full Disk Access:**

1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Click the **+** button (you may need to unlock with your password first)
3. Navigate to **Applications** → **Utilities** → select **Terminal** → click **Open**
4. Terminal now appears in the list with a toggle — make sure it's **ON**
5. **Quit Terminal completely** (`⌘ + Q`) and reopen it
6. Run the command again:

```bash
sudo xattr -cr /Applications/AI\ Debate\ Council.app
```

It should now succeed with no errors. After this, double-click the app normally.

**Alternative if you don't want to grant Full Disk Access:**

Use the System Settings method instead — no Terminal needed:

1. Open **System Settings** → **Privacy & Security**
2. Scroll down to the Security section
3. You'll see "AI Debate Council was blocked" — click **Open Anyway**
4. Enter your password and click **Open**

### Quick Fix for All Gatekeeper Issues

If any of the above dialogs keep appearing, this single Terminal command fixes them all:

```bash
sudo xattr -cr /Applications/AI\ Debate\ Council.app
```

> **Getting "Operation not permitted"?** See [xattr: Operation not permitted](#xattr-operation-not-permitted-even-with-sudo) above — you need to grant Terminal Full Disk Access first.

This removes the macOS quarantine attribute from the app. It is safe and you only need to run it once. After this, double-clicking the app works normally with no security prompts.

---

## Python Issues

### Python 3.10+ Not Found

Check your Python version:

```bash
python --version
python3 --version
python3 --version
```

The backend requires Python 3.10+. If `python3` is not found:

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
py -3 --version
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install python3 python3-venv
```

### Wrong Python Version in Virtual Environment

If you created the virtual environment with the wrong Python version:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

On Windows:

```powershell
Remove-Item .venv -Recurse -Force
py -3 -m venv .venv
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
cd "/path/to/AI Debate Council - MultiAI System - CodeX"
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

You can also activate the virtual environment first and then use `python -m uvicorn ...`, but the explicit `.venv/bin/python -m uvicorn ...` command is the safest copy-paste version.

If you get `ModuleNotFoundError: No module named 'backend'`, you are not in the project root.

### One-command launcher does not start

If you are using the new one-command launcher:

```bash
.venv/bin/python dev.py
```

and it exits immediately:

1. Make sure both backend and frontend dependencies are installed.
2. Make sure `frontend/node_modules` exists. If not:

```bash
cd frontend
npm install
cd ..
```

3. Make sure `.venv` exists and includes Uvicorn:

```bash
python -m pip install -r backend/requirements.txt
```

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

### WebSocket Auto-Reconnect

The frontend automatically retries the WebSocket connection up to 2 times (with a 1.2-second delay) if the initial connection fails before the server starts responding. You will see a status message like "Connection failed. Retrying (1/2)..." in the UI. If all retries fail, the error is displayed.

On the backend side, `safe_send_json()` gracefully handles client disconnects so the server does not crash if you close the browser tab mid-debate.

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

- Lowering Debate rounds or Discussion Messages Per Team in Chat Settings.
- Setting debaters per team to 2 or 3. Four debaters per team produces a longer professional flow.
- Keeping response length concise for Critic, Researcher, and Examiner roles.

### Message Too Long

The app enforces a 5500-character limit on user messages. The frontend shows a live character counter below the text area. At 5000 characters a warning appears; above 5500 the Send button is disabled. Shorten your message or split it into multiple messages.

### Response Gets Truncated

If a message ends with "_Response reached the max-token limit..._":

1. Go to Chat Settings.
2. Find the agent role whose response was truncated.
3. Increase its Max tokens value (up to 2000).

The system automatically attempts one continuation when a response is truncated, but very long responses may still hit the combined limit.

### Multi-Judge Panel Is Slow or Expensive

Judge Panel Size can be set to 1, 3, or 5 in Chat Settings → Judgment Quality. A 3-judge panel makes three independent Judge calls before the final consensus message; a 5-judge panel makes five. This improves robustness, but it costs more and takes longer. Use 1 Judge for quick testing, and 3 or 5 Judges when verdict quality matters.

### Final Verdict Mentions Analytics Weight

This is expected. The Judge system combines the AI Judge or panel votes with the configured Analytics Weight. A low weight keeps the AI verdict dominant. A higher weight lets tracked signals such as Bayesian stance, challenge resolution, evidence quality, and scorecard records influence the final winner.

### I Disagree With the Judge

Open Debate Intelligence → Verdict Review. You can:

- **Challenge** the verdict, which records your objection without changing charts.
- **Override** the winner, which updates saved statistics such as Win Rate by Team.

The original Judge message is never rewritten. The override is stored separately in debate metadata and Debate Intelligence.

If the Verdict Review controls do not appear, check Chat Settings → Judgment Quality → Allow Verdict Challenge / Override.

### Practice Mode Does Not Start

AI vs Human Debate Training is chosen when the chat is created. Existing chats cannot change modes. Create a new chat, choose AI vs Human Debate Training in the setup modal, pick an Overall Model, and send a debate topic. The app will ask whether you want to be Pro, Con, or Auto.

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

### GitHub Models Tokens

GitHub Models routing is intentionally not supported. Use direct provider keys such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `MINIMAX_API_KEY`, or `MOONSHOT_API_KEY`. This avoids false "unlocked" states where GitHub lists a model but the inference endpoint rejects the exact model ID.

### Cost Estimates Look Old or Incomplete

- The app now tries to refresh supported model prices from OpenRouter's model catalog before falling back to the local price table.
- If you have an `OPENROUTER_API_KEY`, the backend includes it for the pricing lookup request. This affects pricing lookup only, not debate routing.
- If your machine cannot reach OpenRouter, the UI will still show a cost estimate, but it will mention the local fallback price source.
- If a model has no trusted live match and no local fallback price, the UI warns that totals exclude that model instead of pretending it cost `$0`.

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

- **Reduce discussion length**: Lower Debate rounds or Discussion Messages Per Team in Chat Settings.
- **Reduce debaters per team**: 2 debaters per team gives a shorter Advocate/Critic flow. 4 debaters per team adds Researchers and Examiners, so it takes longer.
- **Use faster models**: `gpt-4o-mini`, `claude-haiku-4-5`, `gemini-2.5-flash-lite`, and `llama-3.3-70b` are generally faster than their larger counterparts.
- **Use Groq**: Groq's inference is very fast for Llama models.
- **Increase timeout**: If turns are timing out, increase `LITELLM_TIMEOUT_SECONDS` in `.env`.

### Session Charts Are Empty

The session-level charts (Win Rate, Cost by Phase, Debate Duration, Messages per Role, Citations) populate from saved debate data. They require at least one completed debate. The Cost by Phase chart requires cost tracking data from model calls — mock mode records zero-cost entries, so the chart may appear empty until real model calls are made.

### Analytics Are Slow

The analytics engine is lightweight (pure Python, no ML dependencies) and processes after each turn. If the debate has many turns with long content, analytics may take a moment. This is normal and does not block streaming.

### High Memory Usage

SQLite keeps the database in memory while connections are open. For very large databases with thousands of debates:

- Delete old sessions you no longer need.
- Or reset the database: `rm -f backend/data/debate_council.db*` and restart.

## Windows-Specific Issues

### `python` Command Not Found

On Windows, use `py -3` instead of `python3`:

```powershell
py -3 -m venv .venv
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

### `python3` Not Found After Homebrew Install

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

## Desktop App (Electron) Issues

### App Shows "Python Environment Not Found" or "Python 3.10 or later is required"

The app auto-provisions the Python environment on first launch. If you see this error, it means the app could not find Python 3.10+ on your system.

**Fix:** Install Python 3.10 or newer from [python.org/downloads](https://www.python.org/downloads/), then relaunch the app.

On macOS, if you installed Python via Homebrew but the app can't find it, try launching from Terminal:

```bash
open /Applications/AI\ Debate\ Council.app
```

If you want to set up the environment manually instead of letting the app do it:

**macOS:**

```bash
cd ~/Library/Application\ Support/ai-debate-council/backend-env
python3 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r /Applications/AI\ Debate\ Council.app/Contents/Resources/app-content/backend/requirements.txt
```

**Windows:**

```powershell
cd "$env:APPDATA\ai-debate-council\backend-env"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --no-cache-dir -r "$env:LOCALAPPDATA\Programs\ai-debate-council\resources\app-content\backend\requirements.txt"
```

### App Shows "Startup Error: Server Did Not Start"

This means the backend or frontend failed to start within the timeout period. The servers run as invisible background processes, so there is no terminal window to check. Instead:

1. Python 3.10+ is installed and the `.venv` exists inside the app content directory.
2. Node.js 20+ is installed and `frontend/node_modules` exists.
3. No other process is using port 8000 or 6001.
4. The `.env` file exists (copy from `.env.example`) with at least one API key or `MOCK_LLM_RESPONSES=true`.
5. Try running the backend manually from a terminal to see error output:

**macOS:**

```bash
cd /Applications/AI\ Debate\ Council.app/Contents/Resources/app-content
source .venv/bin/activate
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

**Windows:**

```powershell
cd "$env:LOCALAPPDATA\Programs\ai-debate-council\resources\app-content"
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Splash Screen Has No Close Button

The splash screen should show a close button (red circle on macOS, × button on Windows). If you do not see it, you may be running an older version of the app. Download the latest installer from [Releases](https://github.com/Evan1108-Coder/AI-Debate-Council/releases).

Closing the splash screen during startup cleanly quits the app and terminates all background server processes.

### App Only Works When Terminal Is Open

If the app fails to start servers unless a terminal window is open, the app may not be finding Python or Node.js. The app includes PATH detection for common install locations (`/opt/homebrew/bin`, `/usr/local/bin`, nvm directories), but if your tools are installed in non-standard locations, launch the app from a terminal instead:

```bash
open /Applications/AI\ Debate\ Council.app
```

This inherits your shell's full PATH. If the problem persists, verify that Python 3 and Node.js are installed and accessible.

### App Window Is Blank

If the Electron window opens but shows nothing:

1. Press `Cmd+Shift+I` (macOS) or `Ctrl+Shift+I` (Windows) to open DevTools.
2. Check the Console tab for errors.
3. Verify the backend is running: open `http://localhost:8000/health` in a regular browser.
4. Verify the frontend is running: open `http://localhost:6001` in a regular browser.

### "macOS Cannot Verify That This App Is Free From Malware"

See [macOS Gatekeeper Blocks the App](#macos-gatekeeper-blocks-the-app) for all Gatekeeper scenarios including this one, the "正在验证" spinner, and the "app is damaged" dialog.

### Ports Already In Use

If ports 8000 or 6001 are already occupied, the Electron app will assume those servers are already running and connect to them. This is usually fine if you are running the web version alongside the desktop app. If the ports are used by unrelated processes, stop those processes first:

```bash
# macOS/Linux
lsof -ti:8000 | xargs kill
lsof -ti:6001 | xargs kill

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Dark Mode Does Not Apply

The app supports Light, Dark, and System themes via **Council Settings > Appearance > Theme**.

If dark mode does not apply:

1. Make sure the backend is running — the theme is stored server-side and fetched on load.
2. Clear your browser/Electron cache if a stale localStorage value (`adc-theme`) overrides the server setting.
3. If using "System" mode, check that your OS dark mode preference is set correctly.

### Building the Desktop App From Source

See the [Desktop App section in README.md](README.md#desktop-app-this-branch) for build instructions.
