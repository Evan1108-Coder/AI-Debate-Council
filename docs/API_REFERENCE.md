# API Reference

## REST Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check. Returns status, database path, active debate count. |
| `GET` | `/api/models` | List unlocked models, provider summaries, mock mode status. |
| `GET` | `/api/sessions` | List all sessions, sorted by last updated. |
| `POST` | `/api/sessions` | Create a new session. Returns 409 if at the 10-session limit. |
| `DELETE` | `/api/sessions` | Delete all chat sessions while keeping universal experience/profile data. |
| `PATCH` | `/api/sessions/{session_id}` | Rename a session. Body: `{"name": "New Name"}`. |
| `DELETE` | `/api/sessions/{session_id}` | Delete a session and all its data. |
| `POST` | `/api/sessions/{session_id}/clear-history` | Hide visible messages and debates (preserves memory). |
| `POST` | `/api/sessions/{session_id}/clear-memory` | Delete all debates and messages for a session. |
| `GET` | `/api/sessions/{session_id}/messages` | List visible messages for a session. |
| `GET` | `/api/sessions/{session_id}/debates` | List visible debates for a session. |
| `PATCH` | `/api/sessions/{session_id}/debates/{debate_id}` | Rename a debate. Body: `{"name": "New Name"}`. |
| `DELETE` | `/api/sessions/{session_id}/debates/{debate_id}` | Hide a debate's statistics (messages remain). |
| `GET` | `/api/sessions/{session_id}/settings` | Get session settings. |
| `PATCH` | `/api/sessions/{session_id}/settings` | Update session settings. Body: partial settings object. |
| `GET` | `/api/sessions/{session_id}/analytics?debate_id=...` | Get analytics for a session's latest or specified debate. |
| `GET` | `/api/sessions/{session_id}/intelligence?debate_id=...` | Get Claim Ledger, Challenge Tracker, Evidence Ledger, Judge Scorecard, team rooms, and verdict review records. |
| `GET` | `/api/sessions/{session_id}/practice-state` | Get whether an AI vs Human practice debate is currently active in the session. |
| `POST` | `/api/sessions/{session_id}/debates/{debate_id}/feedback` | Save optional post-debate user feedback for future experience records. |
| `POST` | `/api/sessions/{session_id}/debates/{debate_id}/verdict-review` | Save a verdict challenge or winner override. |
| `GET` | `/api/council-settings` | Get universal Council Settings. |
| `PATCH` | `/api/council-settings` | Update universal Council Settings. |
| `POST` | `/api/council-settings/reset-agent-experience` | Reset universal agent identity records with confirmation. |
| `GET` | `/api/ai-debater-experiences` | Get the global AI identity memory view used by the AI Debater Experiences sidebar page. |
| `GET` | `/api/user-debate-profile` | Get the AI vs Human Debate Training profile. |
| `GET` | `/api/user-debate-profile/overview` | Get the global training dashboard view with recommendations and recent practice history. |
| `POST` | `/api/user-debate-profile/reset` | Reset the user debate profile with confirmation. |
| `POST` | `/api/runtime-diary` | Record a runtime diary entry. Body: `{"source": "...", "event": "...", "detail": "...", "session_id": "..."}`. |

## WebSocket

| Path | Description |
| --- | --- |
| `ws://localhost:8000/ws/debates/{session_id}` | Bidirectional WebSocket for debates and chat. |

Send `{"type": "start_interaction", "topic": "...", "model": "model-name"}` to begin. The backend classifies intent and runs either a debate, a chat, or an AI vs Human practice turn, streaming events back.

In practice mode, send `{"type": "end_practice_debate", "model": "model-name"}` to end the practice debate and trigger Judge Assistant, Judge, and Debate Trainer.
