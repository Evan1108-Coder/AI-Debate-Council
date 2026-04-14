# Troubleshooting Guide

Having issues? Find your problem below. If your issue isn't listed, see the bottom of this page for more help.

---

## Installation & Setup Issues

### "python: command not found" or "python3: command not found"

**Symptom:** You run `python` or `python3` and get `zsh: command not found: python` (Mac) or `'python' is not recognized` (Windows).

**Why:** Python isn't installed, or it's not in your system PATH.

**Fix:**

- **macOS:** Use `python3` instead of `python`. macOS does not include a `python` command by default -- you must use `python3`. If even `python3` doesn't work, install Python:
  - Option A: `brew install python3` (if you have Homebrew)
  - Option B: Download from https://www.python.org/downloads/ and run the installer
  - After installing, **close and reopen your terminal**, then try again.

- **Windows:** Download Python from https://www.python.org/downloads/. During installation, **check "Add Python to PATH"** on the first screen. If you already installed Python without checking that box, uninstall it and reinstall with the box checked. After installing, **close and reopen your terminal**.

---

### "pip: command not found" or "pip3: command not found"

**Symptom:** `pip install` or `pip3 install` gives "command not found".

**Fix:**
- **macOS:** Use `pip3` instead of `pip`. If neither works, try `python3 -m pip install -r requirements.txt` instead.
- **Windows:** Use `python -m pip install -r requirements.txt` instead.
- Make sure your virtual environment is activated first (you should see `(venv)` in your prompt).

---

### "npm: command not found" or "node: command not found"

**Symptom:** `npm install` or `node --version` gives "command not found".

**Fix:** Install Node.js from https://nodejs.org/ (choose the LTS version). After installing, **close and reopen your terminal**. Both `node` and `npm` should then work.

---

### PowerShell says "running scripts is disabled"

**Symptom:** On Windows PowerShell, activating the virtual environment gives an error about execution policy.

**Fix:** Run this command, then try activating again:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### "No module named venv"

**Symptom:** `python3 -m venv venv` fails with `No module named venv`.

**Fix:** Your Python installation might be missing the venv module. On Ubuntu/Debian Linux, install it with:
```bash
sudo apt install python3-venv
```
On other systems, reinstall Python from https://www.python.org/downloads/.

---

### npm install takes forever or fails with network errors

**Symptom:** `npm install` hangs or shows ETIMEDOUT / ECONNRESET errors.

**Fix:**
1. Check your internet connection
2. If you're behind a corporate firewall or VPN, try disconnecting temporarily
3. Clear npm cache and retry: `npm cache clean --force && npm install`
4. If on slow internet, be patient -- it may take up to 5 minutes

---

### Python 3.14+ / pydantic-core build fails (PyO3 error)

**Symptom:** When running `pip install -r requirements.txt`, you see an error like:
```
error: the configured Python interpreter version (3.14) is newer than PyO3's maximum supported version (3.13)
```
or:
```
Failed building wheel for pydantic-core
```

**Why:** Python 3.14 is very new. The `pydantic-core` package uses Rust bindings (PyO3) that don't support Python 3.14 yet.

**Fix (Recommended):** Use Python 3.13 instead:

- **macOS:**
  ```bash
  brew install python@3.13
  cd backend
  rm -rf venv
  python3.13 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- **Windows:**
  Download Python 3.13 from https://www.python.org/downloads/ and install it (check "Add to PATH"). Then:
  ```bash
  cd backend
  rmdir /s /q venv
  py -3.13 -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  ```

**Alternative (Quick workaround):** Force build with ABI3 compatibility (may have other issues):
```bash
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install -r requirements.txt
```

---

### "ModuleNotFoundError: No module named 'enterprise'"

**Symptom:** When starting the backend or importing litellm, you see:
```
ModuleNotFoundError: No module named 'enterprise'
```
or:
```
ModuleNotFoundError: No module named 'litellm.proxy.enterprise'
```

**Why:** Certain versions of litellm (1.67.3, 1.67.4, 1.68.1, 1.68.2) accidentally introduced an import for an enterprise-only package that isn't included in the open-source PyPI release. This is a known upstream bug ([GitHub issue #10349](https://github.com/BerriAI/litellm/issues/10349)).

**Fix:** The project's `requirements.txt` already pins a working version (`litellm==1.67.2`). If you're seeing this error, you may have installed a different version. Run:
```bash
pip install litellm==1.67.2
```

To verify you have the correct version:
```bash
pip show litellm | grep Version
```
It should show `Version: 1.67.2`.

If you previously ran `pip install litellm` without a version (which installs the latest), that's likely how the broken version got installed. Always use `pip install -r requirements.txt` to get the pinned versions.

---

### "No module named 'cgi'" (Python 3.13+)

**Symptom:** When importing litellm, you see:
```
ModuleNotFoundError: No module named 'cgi'
```

**Why:** Python 3.13 removed the deprecated `cgi` module. Some older litellm versions depend on it.

**Fix:** Make sure you're using the pinned version:
```bash
pip install litellm==1.67.2
```

---

## Backend Issues

### Backend won't start / ModuleNotFoundError

**Symptom:** `ModuleNotFoundError: No module named 'fastapi'` (or any other module) when running `python3 main.py`.

**Why:** The Python dependencies aren't installed, or the virtual environment isn't active.

**Fix:**
1. Make sure you're in the `backend` folder: `cd backend`
2. Activate the virtual environment:
   - macOS/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
3. You should see `(venv)` at the start of your prompt
4. Install dependencies: `pip3 install -r requirements.txt` (Mac/Linux) or `pip install -r requirements.txt` (Windows)
5. Try starting the backend again: `python3 main.py` (Mac/Linux) or `python main.py` (Windows)

---

### Missing .env file / "No API keys configured"

**Symptom:** The backend starts but no models work, or you see warnings about missing API keys in the terminal.

**Why:** You haven't created the `.env` file yet, or it's in the wrong location.

**Fix:**
1. Make sure you're in the `backend` folder
2. Copy the example file: `cp .env.example .env` (Mac/Linux) or `copy .env.example .env` (Windows)
3. Open `.env` in a text editor and add at least one API key
4. Restart the backend (Ctrl+C, then `python3 main.py` again)

The `.env` file must be in the `backend/` folder (same folder as `main.py`).

---

### Invalid or expired API key errors

**Symptom:** During a debate, you see errors like:
```
AuthenticationError: Invalid API key
```
or:
```
Error: 401 Unauthorized
```
or:
```
RateLimitError: You exceeded your current quota
```

**Why:** Your API key is wrong, expired, or out of credits.

**Fix:**
1. Double-check your API key in `backend/.env` -- make sure there are **no extra spaces** before or after the key
2. Make sure the key is on the correct line (e.g., OpenAI key goes on the `OPENAI_API_KEY=` line, not the `ANTHROPIC_API_KEY=` line)
3. Verify the key works by logging into the provider's dashboard:
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/settings/keys
   - Google: https://aistudio.google.com/apikey
   - Groq: https://console.groq.com/keys
   - MiniMax: https://platform.minimaxi.com/
   - Moonshot: https://platform.moonshot.cn/console/api-keys
4. Check if you have billing/credits set up -- most providers require a payment method
5. After fixing the key, **restart the backend** (Ctrl+C, then start again)

---

### "Address already in use" (port 8000)

**Symptom:** Backend fails to start with `[Errno 48] Address already in use` or similar.

**Why:** Something else is already using port 8000, or a previous instance of the backend is still running.

**Fix:**
1. Check if you have another terminal running the backend -- if so, stop it with `Ctrl+C` first
2. Find and kill the process using port 8000:
   - macOS/Linux: `lsof -i :8000` then `kill <PID>`
   - Windows: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`

---

### "Address already in use" (port 3000)

**Symptom:** Frontend fails to start with port 3000 already in use.

**Fix:** Same approach as port 8000 above, but for port 3000:
- macOS/Linux: `lsof -i :3000` then `kill <PID>`
- Windows: `netstat -ano | findstr :3000` then `taskkill /PID <PID> /F`

---

### Database locked errors

**Symptom:** `database is locked` error in backend logs.

**Fix:**
1. Make sure only one instance of the backend is running
2. If the issue persists, stop the backend, delete `backend/debate_council.db`, then restart

---

### Database corrupted / SQLite errors

**Symptom:** Errors like `sqlite3.DatabaseError: database disk image is malformed` or `OperationalError: no such table`.

**Fix:** Delete the database file and restart. The backend will recreate it automatically:
- macOS/Linux: `rm backend/debate_council.db`
- Windows: `del backend\debate_council.db`

Note: this will delete all saved debate sessions.

---

### CORS errors in browser console

**Symptom:** Browser console shows errors like:
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Why:** This usually means the backend isn't running, or a browser extension is interfering.

**Fix:**
1. Make sure the backend is running on port 8000
2. Try disabling browser extensions (especially ad blockers or privacy extensions) temporarily
3. Try a different browser or incognito/private window
4. If the issue persists, clear your browser cache

---

## Frontend Issues

### Frontend shows "Failed to connect to backend"

**Symptom:** Red error banner at top of page when you open http://localhost:3000.

**Fix:**
1. Make sure the backend is running in another terminal (you should see the Uvicorn log output)
2. Make sure the backend is on port 8000 (check the Uvicorn output)
3. If you changed the backend port, update `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
4. Try refreshing the page

---

### WebSocket connection failed

**Symptom:** "WebSocket connection failed. Is the backend running?" when starting a debate.

**Fix:**
1. Verify the backend is running (check the other terminal)
2. Try refreshing the browser page
3. If using a VPN, firewall, or proxy, ensure WebSocket connections are allowed on port 8000
4. Check browser console (F12 > Console tab) for detailed error messages

---

### Page is blank or shows errors

**Symptom:** http://localhost:3000 shows a blank page or React error overlay.

**Fix:**
1. Open browser DevTools (F12) and check the Console tab for errors
2. Make sure `npm install` completed successfully (no errors)
3. Try stopping the frontend (`Ctrl+C`) and running `npm run dev` again
4. If that doesn't help, delete `frontend/node_modules` and `frontend/.next`, then run `npm install` and `npm run dev` again:
   ```bash
   rm -rf node_modules .next    # Mac/Linux
   # rmdir /s /q node_modules .next   # Windows
   npm install
   npm run dev
   ```

---

### Frontend build errors / "Module not found"

**Symptom:** `npm run dev` fails with errors like `Module not found: Can't resolve '...'` or TypeScript errors.

**Fix:**
1. Make sure you ran `npm install` first
2. Delete `node_modules` and reinstall:
   ```bash
   rm -rf node_modules    # Mac/Linux
   # rmdir /s /q node_modules   # Windows
   npm install
   ```
3. If the error mentions a specific missing package, install it: `npm install <package-name>`
4. Make sure you're using Node.js 18 or higher: `node --version`

---

### "EACCES permission denied" during npm install

**Symptom:** `npm install` fails with permission errors on Mac/Linux.

**Fix:**
- **Don't use `sudo npm install`** (this can cause more problems). Instead, fix npm permissions:
  ```bash
  sudo chown -R $(whoami) ~/.npm
  ```
- Then retry: `npm install`

---

## Debate Issues

### Model API errors during debate

**Symptom:** `[Model error: ...]` appears in debate messages instead of debater responses.

**Fix:**
1. Check that the correct API key is set in `backend/.env` for the model you selected
2. Verify your API key has sufficient credits/quota
3. Some models may have rate limits -- try again after a moment
4. Check the backend terminal for detailed error messages
5. Try a different model

---

### "Maximum 10 chat sessions reached"

**Symptom:** Can't create new sessions.

**Fix:** Delete existing sessions you no longer need. Click the trash icon on any session in the sidebar.

---

### "Maximum concurrent debates (3) reached"

**Symptom:** Can't start a new debate while others are running.

**Fix:** Wait for one of the active debates to complete, or refresh the page if a debate seems stuck.

---

### Debate gets stuck / hangs mid-response

**Symptom:** A debate stops streaming and nothing happens for over a minute.

**Fix:**
1. Check the backend terminal for timeout or API errors
2. Some larger models (like GPT-5.4-pro) may take 30+ seconds per response -- be patient
3. If truly stuck, refresh the page, delete the stuck session, and create a new one

---

### LiteLLM model not found

**Symptom:** Error like `litellm.exceptions.BadRequestError: ... model not found`.

**Fix:**
1. The model may not be available with your API key tier
2. Try a different model (e.g., switch from gpt-5.4-pro to gpt-4o)
3. Check [LiteLLM docs](https://docs.litellm.ai/docs/providers) for supported models

---

### Wrong model responds / model mismatch

**Symptom:** You selected one model but the responses seem to come from a different one.

**Why:** This shouldn't happen with the current architecture. Each model name maps to a specific LiteLLM provider string in `backend/models.py`.

**Fix:**
1. Check the backend terminal for the actual model being called
2. Restart the backend to ensure it picks up the latest code
3. If the issue persists, open a GitHub issue

---

### Session numbering seems off

**Info:** This is by design. Session numbers always increment and never reuse numbers. Example: if you create sessions #1 through #5, then delete #3, the next new session will be #6 (not #3). The counter only resets to #1 when **all** sessions are deleted.

---

## Quick Reference: Common Fixes

| Problem | Quick Fix |
|---------|-----------|
| `python: command not found` | Use `python3` on Mac. Install Python on Windows (check "Add to PATH"). |
| `pip: command not found` | Use `pip3` on Mac, or `python3 -m pip` |
| `npm: command not found` | Install Node.js from https://nodejs.org/ |
| `No module named 'enterprise'` | `pip install litellm==1.67.2` |
| `No module named 'fastapi'` | Activate venv, then `pip install -r requirements.txt` |
| Missing .env file | `cp .env.example .env` and add your API keys |
| API key errors (401) | Check key in `.env`, verify on provider dashboard |
| Port already in use | Kill the process: `lsof -i :8000` then `kill <PID>` |
| Database errors | Delete `debate_council.db` and restart |
| Frontend blank page | Delete `node_modules` and `.next`, then `npm install` |
| PyO3 / Python 3.14 error | Use Python 3.13 instead |

---

## Still Having Issues?

1. **Check the backend terminal** for detailed error logs -- most errors show up there
2. **Open browser DevTools** (press F12) and check the Console and Network tabs
3. **Search existing issues** on [GitHub](https://github.com/Evan1108-Coder/AI-Debate-Council/issues)
4. **Open a new issue** if your problem isn't listed
