# Setup

These steps assume you are working from the project root:

```text
AI Debate Council - MultiAI System - CodeX
```

## Requirements

- Python 3.13
- Node.js 20 or newer
- npm 10 or newer
- At least one provider API key for real debates, unless `MOCK_LLM_RESPONSES=true`

## macOS

1. Install Python 3.13.

   With Homebrew:

   ```bash
   brew install python@3.13
   ```

   Or install it from `https://www.python.org/downloads/`.

2. Create and activate a virtual environment from the project root.

   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   ```

3. Install backend dependencies.

   ```bash
   python -m pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```

4. Create the environment file.

   ```bash
   cp .env.example .env
   ```

5. Add API keys to `.env`.

   Add only provider keys, such as:

   ```text
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   ```

   One provider key unlocks all models from that provider. For example, one OpenAI key unlocks `gpt-5.4-pro`, `gpt-5.4-mini`, `gpt-4o`, and `gpt-4o-mini`. The frontend dropdown shows only unlocked models.

6. Start the backend.

   ```bash
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. Install frontend dependencies in a second terminal.

   ```bash
   cd frontend
   npm install
   ```

8. Start the frontend.

   ```bash
   npm run dev -- -p 6001
   ```

9. Open the app.

   ```text
   http://localhost:6001
   ```

## Windows PowerShell

1. Install Python 3.13 from `https://www.python.org/downloads/`.

   During install, enable the option to add Python to PATH.

2. Create and activate a virtual environment from the project root.

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   .\.venv\Scripts\Activate.ps1
   ```

3. Install backend dependencies.

   ```powershell
   python -m pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```

4. Create the environment file.

   ```powershell
   Copy-Item .env.example .env
   ```

5. Add API keys to `.env`.

   Add only provider keys. Do not add model names. The frontend dropdown shows only models unlocked by the keys you provide.

6. Start the backend.

   ```powershell
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. Install frontend dependencies in a second PowerShell window.

   ```powershell
   cd frontend
   npm install
   ```

8. Start the frontend.

   ```powershell
   npm run dev -- -p 6001
   ```

9. Open:

   ```text
   http://localhost:6001
   ```

## Optional Frontend Environment

The frontend defaults to:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

If the backend runs somewhere else, create `frontend/.env.local`:

```text
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

## Mock Mode

To test the app without model API calls:

```text
MOCK_LLM_RESPONSES=true
```

Restart the backend after changing `.env`.
