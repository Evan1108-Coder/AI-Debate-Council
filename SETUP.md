# Setup — AI Debate Council

A complete beginner-friendly guide. Follow every step in order. If anything goes wrong, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

This project supports two deployment modes from a single codebase. Choose one:

| Mode | Best For | Requirements |
| --- | --- | --- |
| **[Web Application](#web-application-setup)** | Development, custom hosting, Linux | Python 3.13, Node.js 20+, npm 10+ |
| **[Desktop Application](#desktop-application-setup)** | End users who want a native app | Python 3.10+ (Node.js not required) |

Both modes need at least one AI provider API key — or set `MOCK_LLM_RESPONSES=true` to test without one.

---

## Web Application Setup

### macOS

#### Step 1: Install Python 3.13

With Homebrew:

```bash
brew install python@3.13
```

Or download from [python.org/downloads](https://www.python.org/downloads/).

Verify:

```bash
python3.13 --version
```

#### Step 2: Clone the Repository

```bash
git clone https://github.com/Evan1108-Coder/AI-Debate-Council.git
cd AI-Debate-Council
```

#### Step 3: Create and Activate a Virtual Environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

#### Step 4: Install Backend Dependencies

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

This installs FastAPI, Uvicorn, LiteLLM, and python-dotenv.

#### Step 5: Create the Environment File

```bash
cp .env.example .env
```

#### Step 6: Add API Keys

Open `.env` in any text editor and add at least one provider API key:

```text
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

One provider key unlocks all models from that provider. For example, one `OPENAI_API_KEY` unlocks `gpt-5.4-pro`, `gpt-5.4-mini`, `gpt-4o`, and `gpt-4o-mini`. The frontend dropdown shows only unlocked models.

**Do not put model names in `.env`.** The app detects models automatically from your API keys.

See [ENVREADME.md](ENVREADME.md) for the full list of 21 models across 6 providers.

#### Step 7: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

#### Step 8: Start the Whole App in One Terminal (Recommended)

```bash
.venv/bin/python dev.py
```

This starts the backend on `8000` and the frontend on `6001` together.

#### Step 9: Or Start the Backend and Frontend Separately

Backend:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

This command deliberately uses the Python inside `.venv`, so it still works if your terminal says `uvicorn: command not found`.

Verify it works:

```text
http://localhost:8000/health
```

Should return `{"status":"ok","database":"...","active_debates":0}`.

Check your models:

```text
http://localhost:8000/api/models
```

Frontend (new terminal):

```bash
cd frontend
npm run dev -- -p 6001
```

#### Step 10: Open the App

```text
http://localhost:6001
```

Click the **+** button in the sidebar to create your first session. The setup modal lets you choose:

- **AI vs AI Debate**: the Pro and Con council debate each other.
- **AI vs Human Debate Training**: you debate a Practice Debater and receive Judge, Judge Assistant, and Debate Trainer feedback.

After the chat is created, select an Overall Model from the dropdown and type either a normal message or a debate topic.

### Windows PowerShell

#### Step 1: Install Python 3.13

Download from [python.org/downloads](https://www.python.org/downloads/).

During installation, **check the box to add Python to PATH**.

Verify:

```powershell
py -3.13 --version
```

#### Step 2: Install Node.js

Download from [nodejs.org](https://nodejs.org/). The LTS version (20+) is recommended.

Verify:

```powershell
node --version
npm --version
```

#### Step 3: Clone the Repository

```powershell
git clone https://github.com/Evan1108-Coder/AI-Debate-Council.git
cd AI-Debate-Council
```

#### Step 4: Create and Activate a Virtual Environment

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

#### Step 5: Install Backend Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### Step 6: Create the Environment File

```powershell
Copy-Item .env.example .env
```

#### Step 7: Add API Keys

Open `.env` in any text editor (Notepad, VS Code, etc.) and add at least one provider API key. Do not add model names. See [ENVREADME.md](ENVREADME.md) for details.

#### Step 8: Install Frontend Dependencies

```powershell
cd frontend
npm install
cd ..
```

#### Step 9: Start the Whole App in One PowerShell Window (Recommended)

```powershell
.\.venv\Scripts\python dev.py
```

#### Step 10: Or Start the Backend and Frontend Separately

Backend:

```powershell
.\.venv\Scripts\python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend (new PowerShell window):

```powershell
cd frontend
npm run dev -- -p 6001
```

Open `http://localhost:6001`.

### Linux

The steps are the same as macOS. Install Python 3.13 from your distribution's package manager or from [python.org](https://www.python.org/downloads/). Example for Ubuntu/Debian:

```bash
sudo apt update
sudo apt install python3.13 python3.13-venv
```

Then follow macOS Steps 2–10.

### Optional Frontend Environment

The frontend defaults to connecting to `http://localhost:8000` for the API and `ws://localhost:8000` for WebSocket.

If the backend runs on a different host or port, create `frontend/.env.local`:

```text
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

Restart the frontend dev server after changing `.env.local`.

---

## Desktop Application Setup

The desktop app wraps the same web application in an Electron shell. It starts the Python backend and Next.js frontend as invisible background processes — no terminal window appears. A splash screen shows progress during startup.

### What You Need Before Starting

| Requirement | Why |
| --- | --- |
| **Python 3.10 or newer** | The backend runs on Python |
| **An internet connection** | The app downloads Python packages on first launch |
| **At least one AI provider API key** | To use real AI models (or use mock mode for testing) |

**You do NOT need Node.js.** The desktop app bundles the frontend — no npm commands required.

### Pre-built Installers

Download from [Releases](https://github.com/Evan1108-Coder/AI-Debate-Council/releases):

| Platform | File | Notes |
| --- | --- | --- |
| macOS (Apple Silicon) | `AI Debate Council-1.0.0-arm64.dmg` | M1/M2/M3/M4 Macs |
| macOS (Intel) | `AI Debate Council-1.0.0.dmg` | Intel Macs |
| Windows | `AI Debate Council Setup 1.0.0.exe` | 64-bit Windows |

### macOS

#### Step 1: Install Python

If you already have Python 3.10+, skip to Step 2.

**Option A — Using Homebrew (recommended if you have Homebrew):**

Open **Terminal** (press `⌘ + Space`, type "Terminal", press Enter) and run:

```bash
brew install python@3.13
```

**Option B — Download from python.org:**

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the big yellow "Download Python 3.x.x" button
3. Open the downloaded `.pkg` file
4. Follow the installer — click **Continue** → **Continue** → **Agree** → **Install**
5. Enter your Mac password when asked

**Verify Python is installed** — in Terminal, run:

```bash
python3 --version
```

You should see something like `Python 3.13.x`. Any version 3.10 or higher works.

> **⚠️ "正在验证" (Verifying) dialog?** macOS sometimes shows a "Verifying..." spinner when you open a downloaded file. This is normal — just wait 10-30 seconds. If it takes longer than a minute, right-click the file → Open. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#macos-verifying-dialog) for more help.

#### Step 2: Download the App

Go to the [Releases page](https://github.com/Evan1108-Coder/AI-Debate-Council/releases) and download the correct `.dmg` file:

- **Apple Silicon** (M1 / M2 / M3 / M4 Mac): `AI Debate Council-1.0.0-arm64.dmg`
- **Intel Mac**: `AI Debate Council-1.0.0.dmg`

> **Not sure which Mac you have?** Click the Apple menu () → **About This Mac**. If it says "Apple M1" (or M2, M3, M4), download the **arm64** version. If it says "Intel", download the other one.

#### Step 3: Install the App

1. Double-click the downloaded `.dmg` file
2. A window appears showing the app icon and an Applications folder
3. **Drag** the AI Debate Council icon **into** the Applications folder
4. Wait for the copy to finish
5. Close the `.dmg` window
6. (Optional) Eject the disk image: right-click "AI Debate Council" on your desktop → Eject

#### Step 4: Open the App for the First Time

> **⚠️ This step is important.** Because the app is not signed with an Apple Developer certificate (normal for open-source apps), macOS will try to block it. Follow these steps exactly.

1. Open **Finder** → **Applications**
2. **Right-click** (or Ctrl+click) on **AI Debate Council**
3. Click **Open** from the right-click menu
4. macOS shows a dialog saying "macOS cannot verify that this app is free from malware"
5. Click **Open** in that dialog

**What happens next:** The app icon will bounce in the Dock for 10–30 seconds while macOS runs a security check (called Gatekeeper). During this time you may see a "正在验证…" (Verifying…) spinner and **no app window will appear yet**. This is completely normal — just wait.

> **If the icon bounces for more than 1 minute and nothing opens**, macOS Gatekeeper is stuck. Do this:
>
> 1. Click the bouncing icon in the Dock to bring any hidden dialog to the front
> 2. If no dialog appears, open **System Settings** → **Privacy & Security**
> 3. Scroll down — you will see "AI Debate Council was blocked from use because it is not from an identified developer"
> 4. Click **Open Anyway** → enter your password → click **Open**
>
> If that still doesn't work, open **Terminal** and run:
> ```bash
> sudo xattr -cr /Applications/AI\ Debate\ Council.app
> ```
> Enter your Mac password when asked, then double-click the app normally.
>
> **Getting "Operation not permitted"?** You need to grant Terminal Full Disk Access first: **System Settings** → **Privacy & Security** → **Full Disk Access** → click **+** → add **Terminal** (in Applications/Utilities) → quit and reopen Terminal → run the command again. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#xattr-operation-not-permitted-even-with-sudo) for details.

> **Why right-click?** Double-clicking an unsigned app shows a "move to Trash" dialog with no Open button. Right-clicking gives you the Open option. You only need to do this once — after the first open, double-click works fine.

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#macos-gatekeeper-blocks-the-app) for more Gatekeeper scenarios.

#### Step 5: Wait for First-Time Setup

On the **very first launch**, the app will:

1. Show a splash screen saying "Setting up Python environment…"
2. Create a Python environment (this takes about 10 seconds)
3. Show "Installing [package name]…" for each Python package
4. Start the backend and frontend servers

**This first launch takes 1–3 minutes** depending on your internet speed. Subsequent launches take only a few seconds.

> **⚠️ It looks stuck?** The splash screen should show changing status messages (package names updating). If the same message stays for more than 5 minutes, your internet connection might be slow or blocked. Close the app and try again. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#pip-install-hangs) for more help.

#### Step 6: Set Up Your API Keys

Once the app opens, you need to add at least one AI provider API key:

1. Open Terminal and run:

   ```bash
   cd /Applications/AI\ Debate\ Council.app/Contents/Resources/app-content
   cp .env.example .env
   open -e .env
   ```

2. This opens the `.env` file in TextEdit. Add your API key(s):

   ```text
   OPENAI_API_KEY=sk-your-key-here
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

3. Save the file (`⌘ + S`) and close TextEdit
4. **Quit and relaunch** the app for the keys to take effect

> **Don't have API keys yet?** Set `MOCK_LLM_RESPONSES=true` in the `.env` file to test the app with fake AI responses. No API key needed.

One API key unlocks all models from that provider. See [ENVREADME.md](ENVREADME.md) for the full list of 21 models across 6 providers.

### Windows

#### Step 1: Install Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the big yellow "Download Python 3.x.x" button
3. Run the downloaded `.exe` file
4. **⚠️ IMPORTANT: Check the box that says "Add Python to PATH"** at the bottom of the installer
5. Click **Install Now**
6. Click **Close** when finished

**Verify** — open PowerShell (press `Win + X` → "Windows PowerShell") and run:

```powershell
python --version
```

You should see `Python 3.x.x` (3.10 or higher).

#### Step 2: Download and Install the App

1. Go to the [Releases page](https://github.com/Evan1108-Coder/AI-Debate-Council/releases)
2. Download `AI Debate Council Setup 1.0.0.exe`
3. Run the installer and follow the prompts
4. The app installs and may launch automatically

#### Step 3: First Launch

Same as macOS — the first launch takes 1–3 minutes to set up the Python environment. The splash screen shows progress as packages are installed.

#### Step 4: Set Up Your API Keys

1. Open PowerShell and run:

   ```powershell
   cd "$env:LOCALAPPDATA\Programs\ai-debate-council\resources\app-content"
   Copy-Item .env.example .env
   notepad .env
   ```

2. Add your API key(s), save, and close Notepad
3. Quit and relaunch the app

### Building the Desktop App From Source

```bash
git clone https://github.com/Evan1108-Coder/AI-Debate-Council.git
cd AI-Debate-Council

# Set up backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

# Set up and build frontend
cd frontend && npm install && npx next build && cd ..

# Build the desktop app
cd electron && npm install
npm run build:mac    # macOS .dmg
npm run build:win    # Windows .exe
npm run build:all    # Both platforms
```

Built installers appear in the `electron/dist/` directory.

---

## Mock Mode (Both Deployment Modes)

To test the full UI without real API calls or provider keys:

1. Set in `.env`:

   ```text
   MOCK_LLM_RESPONSES=true
   ```

2. Restart the app (or the backend, for web mode).

3. A `mock-debate-model` will appear in the dropdown. Select it and start a debate. The backend streams fake responses that exercise the full UI flow — debate turns, judge verdict, analytics, and all.

Mock mode is useful for:

- Frontend development without spending API credits.
- Testing the debate flow, settings panel, analytics UI, Debate Intelligence, multi-judge panel display, verdict review, and practice-mode flow.
- Verifying the setup works before adding real API keys.

---

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
python3.13 -m unittest backend.tests.test_costing -v
python3.13 -m unittest backend.tests.test_debate_architecture -v
```

---

## Updating

### Web Version

```bash
cd AI-Debate-Council
git pull

# Reinstall backend dependencies (in case requirements changed)
source .venv/bin/activate   # macOS/Linux
pip install -r backend/requirements.txt

# Reinstall frontend dependencies (in case package.json changed)
cd frontend
npm install
```

Then restart both the backend and frontend.

### Desktop App

Download the latest installer from [Releases](https://github.com/Evan1108-Coder/AI-Debate-Council/releases) and install over the existing version. Your `.env` file and database are preserved.

---

## Uninstalling

### Web Version

```bash
# Stop the backend and frontend (Ctrl+C in both terminals)
# Delete the project folder
rm -rf AI-Debate-Council
```

The SQLite database lives inside the project folder at `backend/data/debate_council.db`, so deleting the project folder removes all data.

### Desktop App

**macOS:** Drag AI Debate Council from Applications to Trash.

**Windows:** Settings → Apps → AI Debate Council → Uninstall.
