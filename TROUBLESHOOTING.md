# Troubleshooting Guide

## Common Issues

### Backend won't start

**Symptom:** `ModuleNotFoundError` when running `python main.py`

**Fix:** Make sure you've activated the virtual environment and installed dependencies:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

---

### Frontend shows "Failed to connect to backend"

**Symptom:** Red error banner at top of page

**Fix:**
1. Make sure the backend is running on port 8000: `python main.py`
2. Check that `NEXT_PUBLIC_API_URL` in `frontend/.env.local` points to `http://localhost:8000`
3. Check for CORS issues in browser console

---

### WebSocket connection failed

**Symptom:** "WebSocket connection failed. Is the backend running?"

**Fix:**
1. Verify backend is running
2. Check browser console for connection errors
3. If using a proxy or firewall, ensure WebSocket connections are allowed on port 8000

---

### Model API errors during debate

**Symptom:** `[Model error: ...]` appears in debate messages

**Fix:**
1. Check that the correct API key is set in `backend/.env` for the model you selected
2. Verify your API key has sufficient credits/quota
3. Some models may have rate limits - try again after a moment
4. Check the backend terminal for detailed error messages

---

### "Maximum 10 chat sessions reached"

**Symptom:** Can't create new sessions

**Fix:** Delete existing sessions you no longer need. Click the trash icon on any session in the sidebar.

---

### "Maximum concurrent debates (3) reached"

**Symptom:** Can't start a new debate

**Fix:** Wait for one of the active debates to complete, or refresh the page if a debate seems stuck.

---

### Session numbering seems off

**Info:** Session numbers increment and never reuse. If you create sessions #1-#5, delete #3, the next session will be #6 (not #3). This is by design. The counter only resets to #1 when ALL sessions are deleted.

---

### Database locked errors

**Symptom:** `database is locked` error in backend logs

**Fix:**
1. Make sure only one instance of the backend is running
2. The database uses WAL mode which should handle concurrent reads well
3. If the issue persists, stop the backend and delete `backend/debate_council.db`, then restart

---

### Debate gets stuck

**Symptom:** A debate seems to hang mid-response

**Fix:**
1. Refresh the page - the debate status will update
2. If the debate is truly stuck, delete the session and create a new one
3. Check the backend terminal for timeout or API errors
4. Some models (especially larger ones) may take 30+ seconds to respond

---

### LiteLLM model not found

**Symptom:** Error like `litellm.exceptions.BadRequestError: ... model not found`

**Fix:**
1. The model may not be available with your API key tier
2. Check [LiteLLM docs](https://docs.litellm.ai/docs/providers) for correct model names
3. Try a different model (e.g., switch from gpt-5.4-pro to gpt-4o)

---

## Still having issues?

1. Check the backend terminal for detailed error logs
2. Open browser DevTools (F12) and check the Console and Network tabs
3. Open an issue on [GitHub](https://github.com/Evan1108-Coder/AI-Debate-Council/issues)
