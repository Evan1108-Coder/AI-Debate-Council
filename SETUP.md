# Setup Guide

A detailed, step-by-step guide to get AI Debate Council running on your computer. Written for beginners -- no prior programming experience required.

This guide will walk you through installing the required tools, downloading the project, and getting everything running. Each step includes what the command does, what you should expect to see, and what to do if something goes wrong.

---

## Before You Start

You'll need **two things** to use this app:

1. **A computer** running macOS, Windows, or Linux
2. **An API key** from at least one AI provider (e.g., OpenAI, Anthropic, Google, Groq, or MiniMax). This is what lets the app talk to AI models. See [ENVREADME.md](ENVREADME.md) for how to get one.

You'll also need to use the **Terminal** (macOS/Linux) or **Command Prompt / PowerShell** (Windows). Don't worry if you've never used it before -- just follow each step exactly as written.

**How to open a terminal:**
- **macOS:** Press `Cmd + Space`, type "Terminal", and press Enter
- **Windows:** Press `Win + R`, type `cmd`, and press Enter (or search "Command Prompt" in Start)
- **Linux:** Press `Ctrl + Alt + T`

---

## Step 0: Check and Install Prerequisites

Before we download the project, we need to make sure you have the right tools installed. Run each check below in your terminal.

### 0a. Check if Git is installed

Git is a tool for downloading and managing code. Run this command:

```bash
git --version
```

**If it works**, you'll see something like:
```
git version 2.39.0
```
The exact number doesn't matter -- any version is fine.

**If you get "command not found":**
- **macOS:** A popup may appear asking to install Xcode Command Line Tools. Click "Install" and wait for it to finish. Then try `git --version` again.
- **Windows:** Download Git from https://git-scm.com/downloads and run the installer. Use all default settings. After installing, **close and reopen your terminal**, then try again.

---

### 0b. Check if Python is installed

Python runs the backend server. Run this command:

**macOS / Linux:**
```bash
python3 --version
```

**Windows:**
```bash
python --version
```

**If it works**, you'll see something like:
```
Python 3.12.4
```
Make sure the version is **3.10 or higher** (the first two numbers should be at least 3.10).

**If you get "command not found":**

- **macOS:** Python 3 usually comes pre-installed on newer Macs. If not:
  - Option A: Install via Homebrew: `brew install python3`
  - Option B: Download from https://www.python.org/downloads/ and run the installer
  - After installing, **close and reopen your terminal**, then try `python3 --version` again.

- **Windows:** Download from https://www.python.org/downloads/ and run the installer. **IMPORTANT:** During installation, check the box that says **"Add Python to PATH"** at the bottom of the first screen. This is critical -- if you miss it, Python won't work from the terminal.
  - After installing, **close and reopen your terminal**, then try `python --version` again.

> **Mac users: IMPORTANT!** On macOS, the command is `python3` (not `python`). Throughout this guide, wherever you see `python`, use `python3` instead. Wherever you see `pip`, use `pip3` instead. This is because macOS reserves the `python` command for an older version.

---

### 0c. Check if Node.js and npm are installed

Node.js runs the frontend (the website you see in your browser). npm is a tool that comes with Node.js for installing JavaScript packages.

```bash
node --version
```

**If it works**, you'll see something like:
```
v20.11.0
```
Make sure the version is **18 or higher**.

Then check npm:
```bash
npm --version
```

You should see a version number like `10.2.0`. Any version is fine.

**If you get "command not found":**
- Download Node.js from https://nodejs.org/ (choose the **LTS** version, which is the recommended stable version)
- Run the installer with default settings
- **Close and reopen your terminal**, then try both commands again

---

### 0d. Quick reference: all prerequisite checks

Here's a summary of all the checks in one place:

| Tool | Check command | Minimum version |
|------|-------------|-----------------|
| Git | `git --version` | Any |
| Python | `python3 --version` (Mac/Linux) or `python --version` (Windows) | 3.10+ |
| pip | `pip3 --version` (Mac/Linux) or `pip --version` (Windows) | Any |
| Node.js | `node --version` | 18+ |
| npm | `npm --version` | Any |

If all five commands show version numbers, you're ready to continue!

---

## Step 1: Download the Project

This command downloads the entire project from GitHub to your computer:

```bash
git clone https://github.com/Evan1108-Coder/AI-Debate-Council.git
```

**What you should see:**
```
Cloning into 'AI-Debate-Council'...
remote: Enumerating objects: ...
remote: Counting objects: 100% ...
Receiving objects: 100% ...
```

Now enter the project folder:

```bash
cd AI-Debate-Council
```

> **Tip:** You can type `ls` (Mac/Linux) or `dir` (Windows) to see the files in the folder. You should see files like `README.md`, `SETUP.md`, `backend/`, `frontend/`, etc.

**If you get an error like "fatal: repository not found":**
- Make sure you typed the URL exactly as shown above
- Make sure you have internet access

---

## Step 2: Set Up the Backend (Python Server)

The backend is the "brain" of the app -- it manages debates, talks to AI models, and stores data.

### 2a. Navigate to the backend folder

```bash
cd backend
```

### 2b. Create a virtual environment

A virtual environment is an isolated space for this project's Python packages, so they don't conflict with other things on your computer. Think of it like a sandbox.

**macOS / Linux:**
```bash
python3 -m venv venv
```

**Windows:**
```bash
python -m venv venv
```

**What you should see:** Nothing! No output means it worked. A new folder called `venv` was created inside the `backend` directory.

**If you get an error:**
- `"python3: command not found"` -- Go back to Step 0b and install Python
- `"No module named venv"` -- Your Python installation might be incomplete. Try reinstalling Python from https://www.python.org/downloads/

### 2c. Activate the virtual environment

This tells your terminal to use the project's isolated Python environment.

**macOS / Linux:**
```bash
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**How to know it worked:** Your terminal prompt should now start with `(venv)`. For example:
```
(venv) yourname@computer backend %
```

If you see `(venv)` at the beginning of your prompt, you're good!

**If PowerShell gives a "running scripts is disabled" error:**
Run this command first, then try activating again:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

> **Remember:** Every time you open a new terminal to work on the backend, you'll need to activate the virtual environment again (run the `source` or `activate` command). If you don't see `(venv)` in your prompt, the virtual environment isn't active.

### 2d. Install Python dependencies

This downloads all the Python libraries the backend needs (FastAPI, LiteLLM, etc.):

**macOS / Linux:**
```bash
pip3 install -r requirements.txt
```

**Windows:**
```bash
pip install -r requirements.txt
```

**What you should see:** A lot of output as packages download and install. It might take 1-2 minutes. At the end, you should see something like:
```
Successfully installed fastapi-0.115.12 uvicorn-0.34.2 litellm-1.67.4 ...
```

**If you get an error:**
- `"pip3: command not found"` -- Make sure your virtual environment is activated (you should see `(venv)` in your prompt)
- Connection errors -- Make sure you have internet access
- Permission errors -- Try adding `--user` at the end: `pip3 install -r requirements.txt --user`

---

## Step 3: Configure API Keys

The app needs API keys to talk to AI models. Without at least one key, debates can't run.

### 3a. Create the .env file

The `.env` file is where you put your secret API keys. We start by copying the example template:

**macOS / Linux:**
```bash
cp .env.example .env
```

**Windows (Command Prompt):**
```bash
copy .env.example .env
```

### 3b. Edit the .env file

Open the `.env` file in any text editor:

- **macOS:** `open -e .env` (opens in TextEdit) or `nano .env` (edit in terminal)
- **Windows:** `notepad .env`
- **Or** just find the file in Finder/Explorer and double-click it

You'll see lines like this:
```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
GROQ_API_KEY=
MINIMAX_API_KEY=
MINIMAX_GROUP_ID=
```

**You only need to fill in keys for the AI provider(s) you plan to use.** For example, if you only have an OpenAI key:

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
GROQ_API_KEY=
MINIMAX_API_KEY=
MINIMAX_GROUP_ID=
```

Leave the other lines empty -- that's fine.

**Save the file** after editing (`Ctrl+S` or `Cmd+S`).

See **[ENVREADME.md](../ENVREADME.md)** for a detailed explanation of each variable and where to get API keys.

> **IMPORTANT:** Never share your `.env` file or API keys with anyone. The `.gitignore` file is already configured to prevent accidentally uploading your keys to GitHub.

---

## Step 4: Start the Backend Server

Make sure you're still in the `backend` folder and your virtual environment is active (you should see `(venv)` in your prompt).

**macOS / Linux:**
```bash
python3 main.py
```

**Windows:**
```bash
python main.py
```

**What you should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

This means the backend is running at `http://localhost:8000`.

**IMPORTANT: Keep this terminal window open!** The backend needs to stay running. You'll open a **new, separate terminal** for the next step.

**If you get errors:**
- `"python3: command not found"` -- Go back to Step 0b
- `"ModuleNotFoundError: No module named 'fastapi'"` -- Your virtual environment isn't active or dependencies aren't installed. Run `source venv/bin/activate` (Mac) or `venv\Scripts\activate` (Windows), then `pip3 install -r requirements.txt`
- `"Address already in use"` -- Another program is using port 8000. Either stop that program, or check TROUBLESHOOTING.md for how to change the port

---

## Step 5: Set Up the Frontend (Website)

**Open a new terminal window** (don't close the backend terminal!).

### 5a. Navigate to the frontend folder

From the project root:
```bash
cd AI-Debate-Council/frontend
```

Or if you're still in the `backend` folder:
```bash
cd ../frontend
```

> **Tip:** If you're not sure where you are, type `pwd` (Mac/Linux) or `cd` (Windows) to see your current location. You should be inside the `frontend` folder.

### 5b. Install frontend dependencies

```bash
npm install
```

**What you should see:** A lot of output as JavaScript packages download. This might take 1-3 minutes on a slower connection. At the end:
```
added 350 packages in 45s
```

The exact numbers will vary -- that's normal.

**If you get errors:**
- `"npm: command not found"` -- Go back to Step 0c and install Node.js
- `"EACCES permission denied"` -- On Mac/Linux, try: `sudo npm install` (you'll need to enter your password)
- Network errors -- Check your internet connection

---

## Step 6: Start the Frontend

Still in the `frontend` folder:

```bash
npm run dev
```

**What you should see:**
```
  ▲ Next.js 16.x.x
  - Local:        http://localhost:3000
  - Environments: .env.local

 ✓ Starting...
 ✓ Ready in 2.5s
```

---

## Step 7: Open the App

Open your web browser (Chrome, Firefox, Safari, Edge -- any modern browser works) and go to:

**http://localhost:3000**

You should see the AI Debate Council interface with a dark sidebar on the left and a welcome screen in the center.

### How to use it:

1. **Create a debate:** Click **"+ New Debate"** in the sidebar
2. **Pick a model:** Use the dropdown at the top right to choose an AI model (only models you have API keys for will work)
3. **Set rounds:** Choose how many debate rounds you want (1-5). More rounds = deeper debate
4. **Enter a topic:** Type any debate topic in the text box at the bottom (e.g., "Should AI replace teachers?", "Is remote work better than office work?")
5. **Start:** Press Enter or click **"Start Debate"**
6. **Watch:** The four debaters will take turns arguing, followed by the Judge's final verdict. Responses stream in real-time, token by token.

---

## Stopping the App

When you're done:

1. Go to the **frontend terminal** and press `Ctrl+C` to stop the frontend
2. Go to the **backend terminal** and press `Ctrl+C` to stop the backend
3. (Optional) Deactivate the virtual environment by typing: `deactivate`

---

## Starting the App Again Later

Every time you want to use the app after the first setup:

**Terminal 1 (Backend):**
```bash
cd AI-Debate-Council/backend
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows
python3 main.py                   # Mac/Linux
# python main.py                  # Windows
```

**Terminal 2 (Frontend):**
```bash
cd AI-Debate-Council/frontend
npm run dev
```

Then open http://localhost:3000 in your browser. Your previous debate sessions will still be there.

---

## Updating to the Latest Version

If there's a new version of the project:

```bash
cd AI-Debate-Council
git pull origin main
cd backend && pip3 install -r requirements.txt
cd ../frontend && npm install
```

Then restart both the backend and frontend.

---

## Resetting the Database

If you want to clear all debate sessions and start fresh, delete the database file:

**macOS / Linux:**
```bash
rm backend/debate_council.db
```

**Windows:**
```bash
del backend\debate_council.db
```

The database will be recreated automatically when you restart the backend.
