import asyncio
import json
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_db, get_next_session_number
from models import (
    AVAILABLE_MODELS,
    CreateSessionRequest,
    RenameSessionRequest,
    StartDebateRequest,
    SessionResponse,
    MessageResponse,
)
from debate import run_debate, can_start_debate, active_debates

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="AI Debate Council", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REST Endpoints ---


@app.get("/api/models")
async def list_models():
    return {"models": AVAILABLE_MODELS}


@app.get("/api/sessions")
async def list_sessions():
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM sessions ORDER BY updated_at DESC"
        )
        rows = await cursor.fetchall()
        return {
            "sessions": [dict(row) for row in rows],
            "active_debates": len(active_debates),
            "max_debates": 3,
        }
    finally:
        await db.close()


@app.post("/api/sessions")
async def create_session(req: CreateSessionRequest = CreateSessionRequest()):
    db = await get_db()
    try:
        # Check max 10 sessions
        cursor = await db.execute("SELECT COUNT(*) as count FROM sessions")
        row = await cursor.fetchone()
        if row[0] >= 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 chat sessions reached. Delete an existing session first.",
            )

        if req.model not in AVAILABLE_MODELS:
            raise HTTPException(status_code=400, detail=f"Invalid model: {req.model}")

        num = await get_next_session_number()
        name = f"Debate Session #{num}"

        cursor = await db.execute(
            "INSERT INTO sessions (name, session_number, model) VALUES (?, ?, ?)",
            (name, num, req.model),
        )
        await db.commit()
        session_id = cursor.lastrowid

        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = await cursor.fetchone()
        return dict(session)
    finally:
        await db.close()


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = await cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return dict(session)
    finally:
        await db.close()


@app.patch("/api/sessions/{session_id}/rename")
async def rename_session(session_id: int, req: RenameSessionRequest):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = await cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        await db.execute(
            "UPDATE sessions SET name = ?, updated_at = datetime('now') WHERE id = ?",
            (req.name, session_id),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        return dict(await cursor.fetchone())
    finally:
        await db.close()


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = await cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session_id in active_debates:
            raise HTTPException(
                status_code=400, detail="Cannot delete a session with an active debate"
            )

        await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await db.commit()
        return {"deleted": True}
    finally:
        await db.close()


@app.get("/api/sessions/{session_id}/messages")
async def get_messages(session_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Session not found")

        cursor = await db.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        )
        rows = await cursor.fetchall()
        return {"messages": [dict(row) for row in rows]}
    finally:
        await db.close()


@app.patch("/api/sessions/{session_id}/model")
async def update_model(session_id: int, req: CreateSessionRequest):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        session = await cursor.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if req.model not in AVAILABLE_MODELS:
            raise HTTPException(status_code=400, detail=f"Invalid model: {req.model}")

        await db.execute(
            "UPDATE sessions SET model = ?, updated_at = datetime('now') WHERE id = ?",
            (req.model, session_id),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        return dict(await cursor.fetchone())
    finally:
        await db.close()


# --- WebSocket for debate streaming ---


async def save_message(session_id: int, role: str, content: str):
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        await db.commit()
    finally:
        await db.close()


@app.websocket("/ws/debate/{session_id}")
async def debate_websocket(websocket: WebSocket, session_id: int):
    await websocket.accept()

    try:
        # Receive debate config
        data = await websocket.receive_json()
        topic = data.get("topic", "")
        model = data.get("model")
        rounds = data.get("rounds", 2)

        if not topic:
            await websocket.send_json({"type": "error", "message": "Topic is required"})
            await websocket.close()
            return

        if not can_start_debate():
            await websocket.send_json({
                "type": "error",
                "message": "Maximum concurrent debates (3) reached. Please wait for a debate to finish.",
            })
            await websocket.close()
            return

        # Get session model if not provided
        if not model:
            db = await get_db()
            try:
                cursor = await db.execute("SELECT model FROM sessions WHERE id = ?", (session_id,))
                row = await cursor.fetchone()
                if row:
                    model = row[0]
                else:
                    model = "gpt-4o"
            finally:
                await db.close()

        # Update session status and topic
        db = await get_db()
        try:
            await db.execute(
                "UPDATE sessions SET status = 'debating', topic = ?, updated_at = datetime('now') WHERE id = ?",
                (topic, session_id),
            )
            await db.commit()
        finally:
            await db.close()

        # Save user message
        await save_message(session_id, "user", topic)

        # Run the debate
        async for event in run_debate(session_id, topic, model, rounds, save_message):
            await websocket.send_json(event)

        # Update session status
        db = await get_db()
        try:
            await db.execute(
                "UPDATE sessions SET status = 'completed', updated_at = datetime('now') WHERE id = ?",
                (session_id,),
            )
            await db.commit()
        finally:
            await db.close()

    except WebSocketDisconnect:
        active_debates.discard(session_id)
        db = await get_db()
        try:
            await db.execute(
                "UPDATE sessions SET status = 'idle', updated_at = datetime('now') WHERE id = ?",
                (session_id,),
            )
            await db.commit()
        finally:
            await db.close()
    except Exception as e:
        active_debates.discard(session_id)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
