# Setup Guide

Step-by-step instructions to get AI Debate Council running on your machine.

## Prerequisites

- **Python 3.10+** -- [Download](https://www.python.org/downloads/)
- **Node.js 18+** -- [Download](https://nodejs.org/)
- **npm** -- Comes with Node.js
- **Git** -- [Download](https://git-scm.com/)
- At least **one API key** from a supported provider (OpenAI, Anthropic, Google, Groq, or MiniMax)

## Step 1: Clone the Repository

```bash
git clone https://github.com/Evan1108-Coder/AI-Debate-Council.git
cd AI-Debate-Council
```

## Step 2: Set Up the Backend

### Create a virtual environment

```bash
cd backend
python -m venv venv
```

### Activate the virtual environment

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

### Install Python dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

```bash
cp .env.example .env
```

Open `backend/.env` in your editor and fill in your API keys. You only need keys for the models you plan to use. For example, if you only want to use GPT models, you just need `OPENAI_API_KEY`.

See **[ENVREADME.md](../ENVREADME.md)** for a detailed explanation of each variable.

## Step 4: Start the Backend

```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
```

The backend API is now running at `http://localhost:8000`.

**Keep this terminal open** and open a new terminal for the frontend.

## Step 5: Set Up the Frontend

```bash
cd frontend
npm install
```

### (Optional) Configure frontend environment

If the backend is running on a different host/port, create `frontend/.env.local`:

```bash
cp .env.example .env.local
```

Edit `NEXT_PUBLIC_API_URL` to point to your backend. The default (`http://localhost:8000`) works if everything is on the same machine.

## Step 6: Start the Frontend

```bash
npm run dev
```

You should see:
```
- Local:   http://localhost:3000
```

## Step 7: Use the App

1. Open **http://localhost:3000** in your browser
2. Click **"+ New Debate"** in the sidebar to create a session
3. Select an AI model from the dropdown (top right)
4. Choose the number of debate rounds (1-5)
5. Type a debate topic and press Enter or click **"Start Debate"**
6. Watch as 4 debaters argue from different perspectives, followed by the Judge's verdict

## Stopping the App

- Press `Ctrl+C` in each terminal to stop the backend and frontend
- Deactivate the virtual environment with: `deactivate`

## Updating

```bash
git pull origin main
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

## Resetting the Database

To start fresh, delete the database file:

```bash
rm backend/debate_council.db
```

The database will be recreated automatically when you restart the backend.
