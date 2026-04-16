# Setup

Step-by-step installation guide for AI Debate Council. For environment variable details, see [ENVREADME.md](ENVREADME.md). For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Requirements

- **Python 3.13** (required — the backend uses Python 3.13 features)
- **Node.js 20** or newer
- **npm 10** or newer
- **At least one provider API key** for real debates (or `MOCK_LLM_RESPONSES=true` for testing)

## macOS

### Step 1: Install Python 3.13

With Homebrew:

```bash
brew install python@3.13
```

Or download from [python.org/downloads](https://www.python.org/downloads/).

Verify:

```bash
python3.13 --version
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/Evan1108-Coder/AI-Debate-Council.git
cd AI-Debate-Council
```

### Step 3: Create and Activate a Virtual Environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### Step 4: Install Backend Dependencies

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

This installs FastAPI, Uvicorn, LiteLLM, and python-dotenv.

### Step 5: Create the Environment File

```bash
cp .env.example .env
```

### Step 6: Add API Keys

Open `.env` in any text editor and add at least one provider API key:

```text
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

One provider key unlocks all models from that provider. For example, one `OPENAI_API_KEY` unlocks `gpt-5.4-pro`, `gpt-5.4-mini`, `gpt-4o`, and `gpt-4o-mini`. The frontend dropdown shows only unlocked models.

**Do not put model names in `.env`.** The app detects models automatically from your API keys.

See [ENVREADME.md](ENVREADME.md) for the full list of 21 models across 6 providers.

### Step 7: Start the Backend

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it works:

```text
http://localhost:8000/health
```

Should return `{"status":"ok","database":"...","active_debates":0}`.

Check your models:

```text
http://localhost:8000/api/models
```

### Step 8: Install Frontend Dependencies (New Terminal)

Open a second terminal window:

```bash
cd AI-Debate-Council/frontend
npm install
```

### Step 9: Start the Frontend

```bash
npm run dev -- -p 6001
```

### Step 10: Open the App

```text
http://localhost:6001
```

Click the **+** button in the sidebar to create your first session, select a model from the dropdown, and type a topic to start a debate.

## Windows PowerShell

### Step 1: Install Python 3.13

Download from [python.org/downloads](https://www.python.org/downloads/).

During installation, **check the box to add Python to PATH**.

Verify:

```powershell
py -3.13 --version
```

### Step 2: Install Node.js

Download from [nodejs.org](https://nodejs.org/). The LTS version (20+) is recommended.

Verify:

```powershell
node --version
npm --version
```

### Step 3: Clone the Repository

```powershell
git clone https://github.com/Evan1108-Coder/AI-Debate-Council.git
cd AI-Debate-Council
```

### Step 4: Create and Activate a Virtual Environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation with a security error:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` in your terminal prompt.

### Step 5: Install Backend Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Step 6: Create the Environment File

```powershell
Copy-Item .env.example .env
```

### Step 7: Add API Keys

Open `.env` in any text editor (Notepad, VS Code, etc.) and add at least one provider API key. Do not add model names. See [ENVREADME.md](ENVREADME.md) for details.

### Step 8: Start the Backend

```powershell
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify: Open `http://localhost:8000/health` in your browser.

### Step 9: Install Frontend Dependencies (New PowerShell Window)

Open a second PowerShell window:

```powershell
cd AI-Debate-Council\frontend
npm install
```

### Step 10: Start the Frontend

```powershell
npm run dev -- -p 6001
```

### Step 11: Open the App

```text
http://localhost:6001
```

## Linux

The steps are the same as macOS. Install Python 3.13 from your distribution's package manager or from [python.org](https://www.python.org/downloads/). Example for Ubuntu/Debian:

```bash
sudo apt update
sudo apt install python3.13 python3.13-venv
```

Then follow macOS Steps 2–10.

## Optional Frontend Environment

The frontend defaults to connecting to `http://localhost:8000` for the API and `ws://localhost:8000` for WebSocket.

If the backend runs on a different host or port, create `frontend/.env.local`:

```text
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

Restart the frontend dev server after changing `.env.local`.

## Mock Mode

To test the full UI without real API calls or provider keys:

1. Set in `.env`:

   ```text
   MOCK_LLM_RESPONSES=true
   ```

2. Restart the backend.

3. A `mock-debate-model` will appear in the dropdown. Select it and start a debate. The backend streams fake responses that exercise the full UI flow — debate turns, judge verdict, analytics, and all.

Mock mode is useful for:

- Frontend development without spending API credits.
- Testing the debate flow, settings panel, and analytics UI.
- Verifying the setup works before adding real API keys.

## Running Tests

The backend includes unit tests that work without API keys:

```bash
# Run all tests
python3.13 -m unittest discover -s backend/tests -v

# Run individual test modules
python3.13 -m unittest backend.tests.test_session_naming -v
python3.13 -m unittest backend.tests.test_model_registry -v
python3.13 -m unittest backend.tests.test_session_settings -v
python3.13 -m unittest backend.tests.test_analytics -v
python3.13 -m unittest backend.tests.test_debate_architecture -v
```

## Updating

To pull the latest changes:

```bash
cd AI-Debate-Council
git pull origin main

# Reinstall backend dependencies (in case requirements changed)
source .venv/bin/activate   # macOS/Linux
pip install -r backend/requirements.txt

# Reinstall frontend dependencies (in case package.json changed)
cd frontend
npm install
```

Then restart both the backend and frontend.

## Uninstalling

To remove everything:

```bash
# Stop the backend and frontend (Ctrl+C in both terminals)

# Delete the project folder
rm -rf AI-Debate-Council
```

The SQLite database lives inside the project folder at `backend/data/debate_council.db`, so deleting the project folder removes all data.
