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

**Symptom:** `python3 -m venv venv` fails.

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
  rm -rf .venv
  python3.13 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

- **Windows:**
  Download Python 3.13 from https://www.python.org/downloads/ and install it (check "Add to PATH"). Then:
  ```bash
  cd backend
  rmdir /s /q .venv
  py -3.13 -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt
  ```

**Alternative (Quick workaround):** Force build with ABI3 compatibility (may have other issues):
```bash
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install -r requirements.txt
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

### "Address already in use" (port 8000)

**Symptom:** Backend fails to start with `[Errno 48] Address already in use` or similar.

**Why:** Something else is already using port 8000, or a previous instance of the backend is still running.

**Fix:**
1. Check if you have another terminal running the backend -- if so, stop it with `Ctrl+C` first
2. Find and kill the process using port 8000:
   - macOS/Linux: `lsof -i :8000` then `kill <PID>`
   - Windows: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`

---

### Database locked errors

**Symptom:** `database is locked` error in backend logs.

**Fix:**
1. Make sure only one instance of the backend is running
2. If the issue persists, stop the backend, delete `backend/debate_council.db`, then restart

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
4. If that doesn't help, delete `frontend/node_modules` and `frontend/.next`, then run `npm install` and `npm run dev` again

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

### Session numbering seems off

**Info:** This is by design. Session numbers always increment and never reuse numbers. Example: if you create sessions #1 through #5, then delete #3, the next new session will be #6 (not #3). The counter only resets to #1 when **all** sessions are deleted.

---

## Still Having Issues?

1. **Check the backend terminal** for detailed error logs -- most errors show up there
2. **Open browser DevTools** (press F12) and check the Console and Network tabs
3. **Search existing issues** on [GitHub](https://github.com/Evan1108-Coder/AI-Debate-Council/issues)
4. **Open a new issue** if your problem isn't listed
