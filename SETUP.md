# Setup (Desktop App)

Step-by-step installation guide for AI Debate Council as a native desktop application. For environment variable details, see [ENVREADME.md](ENVREADME.md). For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

> **Looking for the web version?** Switch to the `master-website-interface` branch for the browser-based application that you run from the terminal.

## Requirements

- **Python 3.13** (required — the backend uses Python 3.13 features)
- **Node.js 20** or newer
- **npm 10** or newer
- **At least one provider API key** for real debates (or `MOCK_LLM_RESPONSES=true` for testing)

The desktop app bundles the backend and frontend source code but not the Python or Node.js runtimes. You need both installed on your system.

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

### Step 2: Install Node.js

Download from [nodejs.org](https://nodejs.org/). The LTS version (20+) is recommended.

```bash
node --version
npm --version
```

### Step 3: Download and Install the App

Download the `.dmg` installer for your Mac from [Releases](https://github.com/Evan1108-Coder/AI-Debate-Council/releases):

- **Apple Silicon** (M1/M2/M3/M4): `AI Debate Council-1.0.0-arm64.dmg`
- **Intel Macs**: `AI Debate Council-1.0.0.dmg`

Open the `.dmg` and drag **AI Debate Council** to the **Applications** folder.

### Step 4: First-Time Setup

Before the first launch, open Terminal and set up the Python environment and frontend dependencies inside the app bundle:

```bash
cd /Applications/AI\ Debate\ Council.app/Contents/Resources/app-content
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

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

One provider key unlocks all models from that provider. For example, one `OPENAI_API_KEY` unlocks `gpt-5.4-pro`, `gpt-5.4-mini`, `gpt-4o`, and `gpt-4o-mini`.

**Do not put model names in `.env`.** The app detects models automatically from your API keys.

See [ENVREADME.md](ENVREADME.md) for the full list of 21 models across 6 providers.

### Step 7: Launch the App

Open **AI Debate Council** from Applications.

If macOS shows "Cannot verify that this app is free from malware":

**Method 1 (Right-click):**

1. Right-click (or Ctrl+click) the app in Applications.
2. Select "Open" from the context menu.
3. Click "Open" in the dialog.

**Method 2 (System Settings):**

1. Open **System Settings** → **Privacy & Security**.
2. Scroll down to the Security section. You will see a message saying "AI Debate Council" was blocked.
3. Click **Open Anyway**.
4. Enter your password when prompted.

You only need to do this once. macOS remembers your choice.

### Step 8: Using the App

The app automatically starts the backend (port 8000) and frontend (port 6001), shows a splash screen while loading, then opens the main window.

Click the **+** button in the sidebar to create your first session. The setup modal lets you choose:

- **AI vs AI Debate**: the Pro and Con council debate each other.
- **AI vs Human Debate Training**: you debate a Practice Debater and receive Judge, Judge Assistant, and Debate Trainer feedback.

After the chat is created, select an Overall Model from the dropdown and type either a normal message or a debate topic.

## Windows

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

### Step 3: Download and Install the App

Download `AI Debate Council Setup 1.0.0.exe` from [Releases](https://github.com/Evan1108-Coder/AI-Debate-Council/releases).

Run the installer and follow the prompts. Choose an installation directory or accept the default.

### Step 4: First-Time Setup

Before the first launch, open PowerShell and set up the Python environment and frontend dependencies:

```powershell
cd "$env:LOCALAPPDATA\Programs\ai-debate-council\resources\app-content"
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
cd frontend; npm install; cd ..
```

If PowerShell blocks activation with a security error:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### Step 5: Create the Environment File

```powershell
Copy-Item .env.example .env
```

### Step 6: Add API Keys

Open `.env` in any text editor (Notepad, VS Code, etc.) and add at least one provider API key. Do not add model names. See [ENVREADME.md](ENVREADME.md) for details.

### Step 7: Launch the App

Open **AI Debate Council** from the Start Menu or Desktop shortcut.

## Building from Source

If you prefer to build the desktop app yourself instead of downloading a pre-built installer:

```bash
git clone -b master-app-interface https://github.com/Evan1108-Coder/AI-Debate-Council.git
cd AI-Debate-Council

# Set up backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Set up frontend
cd frontend && npm install && npx next build && cd ..

# Install Electron dependencies and build
cd electron && npm install
npm run build:mac    # macOS .dmg (arm64 + x64)
npm run build:win    # Windows .exe
npm run build:all    # Both platforms
```

Built installers appear in the `dist/` directory.

### Running in Development Mode

Instead of building an installer, you can run the app directly:

```bash
cd electron
npm start
```

This starts Electron, which launches the backend and frontend servers and opens the app window.

## Mock Mode

To test the full UI without real API calls or provider keys:

1. Set in `.env`:

   ```text
   MOCK_LLM_RESPONSES=true
   ```

2. Relaunch the app.

3. A `mock-debate-model` will appear in the dropdown. Select it and start a debate. The backend streams fake responses that exercise the full UI flow — debate turns, judge verdict, analytics, and all.

## Running Tests

The backend includes unit tests that work without API keys:

```bash
# From the app content directory (or project root if building from source)
python3.13 -m unittest discover -s backend/tests -v
```

## Updating

To update the desktop app, download the latest installer from [Releases](https://github.com/Evan1108-Coder/AI-Debate-Council/releases) and install it over the existing version. Your `.env` file and database will be preserved.

If building from source:

```bash
cd AI-Debate-Council
git pull
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && npx next build && cd ..
cd electron && npm install && npm run build:mac
```

## Uninstalling

### macOS

1. Quit the app.
2. Drag **AI Debate Council** from Applications to the Trash.

### Windows

1. Quit the app.
2. Open Settings → Apps → AI Debate Council → Uninstall.

The SQLite database lives inside the app content directory. Uninstalling removes all data.
