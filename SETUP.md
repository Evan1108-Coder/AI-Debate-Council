# Setup — AI Debate Council (Desktop App)

A complete beginner-friendly guide. Follow every step in order. If anything goes wrong, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

> **Looking for the web version?** Switch to the `master-website-interface` branch.

---

## What You Need Before Starting

| Requirement | Why |
| --- | --- |
| **Python 3.10 or newer** | The backend runs on Python |
| **An internet connection** | The app downloads Python packages on first launch |
| **At least one AI provider API key** | To use real AI models (or use mock mode for testing) |

**You do NOT need Node.js.** The desktop app bundles the frontend — no npm commands required.

---

## macOS Setup

### Step 1: Install Python

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

### Step 2: Download the App

Go to the [Releases page](https://github.com/Evan1108-Coder/AI-Debate-Council/releases) and download the correct `.dmg` file:

- **Apple Silicon** (M1 / M2 / M3 / M4 Mac): `AI Debate Council-1.0.0-arm64.dmg`
- **Intel Mac**: `AI Debate Council-1.0.0.dmg`

> **Not sure which Mac you have?** Click the Apple menu () → **About This Mac**. If it says "Apple M1" (or M2, M3, M4), download the **arm64** version. If it says "Intel", download the other one.

### Step 3: Install the App

1. Double-click the downloaded `.dmg` file
2. A window appears showing the app icon and an Applications folder
3. **Drag** the AI Debate Council icon **into** the Applications folder
4. Wait for the copy to finish
5. Close the `.dmg` window
6. (Optional) Eject the disk image: right-click "AI Debate Council" on your desktop → Eject

### Step 4: Open the App for the First Time

1. Open **Finder** → **Applications**
2. **Right-click** (or Ctrl+click) on **AI Debate Council**
3. Click **Open** from the menu
4. A dialog says "macOS cannot verify that this app is free from malware" — click **Open**

> **Why right-click?** Because the app is not signed with an Apple certificate (this is normal for open-source apps). Double-clicking shows a different dialog that doesn't have the "Open" button. You only need to right-click the very first time.

> **⚠️ If you see "damaged" or "正在验证" and it never finishes**, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md#macos-verifying-dialog).

### Step 5: Wait for First-Time Setup

On the **very first launch**, the app will:

1. Show a splash screen saying "Setting up Python environment…"
2. Create a Python environment (this takes about 10 seconds)
3. Show "Installing [package name]…" for each Python package
4. Start the backend and frontend servers

**This first launch takes 1–3 minutes** depending on your internet speed. Subsequent launches take only a few seconds.

> **⚠️ It looks stuck?** The splash screen should show changing status messages (package names updating). If the same message stays for more than 5 minutes, your internet connection might be slow or blocked. Close the app and try again. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#pip-install-hangs) for more help.

### Step 6: Set Up Your API Keys

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

### Step 7: Start Using the App

1. Click the **+** button in the sidebar to create a new session
2. Choose **AI vs AI Debate** or **AI vs Human Debate Training**
3. Select a model from the **Overall Model** dropdown
4. Type a debate topic and press Enter!

To switch between light and dark mode: open **Council Settings** from the sidebar footer.

---

## Windows Setup

### Step 1: Install Python

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

### Step 2: Download and Install the App

1. Go to the [Releases page](https://github.com/Evan1108-Coder/AI-Debate-Council/releases)
2. Download `AI Debate Council Setup 1.0.0.exe`
3. Run the installer and follow the prompts
4. The app installs and may launch automatically

### Step 3: First Launch

Same as macOS — the first launch takes 1–3 minutes to set up the Python environment. The splash screen shows progress as packages are installed.

### Step 4: Set Up Your API Keys

1. Open PowerShell and run:

   ```powershell
   cd "$env:LOCALAPPDATA\Programs\ai-debate-council\resources\app-content"
   Copy-Item .env.example .env
   notepad .env
   ```

2. Add your API key(s), save, and close Notepad
3. Quit and relaunch the app

---

## Testing Without API Keys (Mock Mode)

To try the app without spending money on API calls:

1. Open the `.env` file (see Step 6 above)
2. Add this line:

   ```text
   MOCK_LLM_RESPONSES=true
   ```

3. Save and relaunch the app
4. A `mock-debate-model` will appear in the model dropdown

Mock mode streams fake responses that exercise the full UI — debate turns, judge verdict, analytics, and all.

---

## Building From Source

If you want to build the desktop app yourself instead of using the pre-built installer:

```bash
git clone -b master-app-interface https://github.com/Evan1108-Coder/AI-Debate-Council.git
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

## Updating

Download the latest installer from [Releases](https://github.com/Evan1108-Coder/AI-Debate-Council/releases) and install over the existing version. Your `.env` file and database are preserved.

## Uninstalling

**macOS:** Drag AI Debate Council from Applications to Trash.

**Windows:** Settings → Apps → AI Debate Council → Uninstall.
