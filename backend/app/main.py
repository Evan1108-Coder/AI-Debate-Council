from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .analytics import analyze_debate
from .config import settings
from .database import Database
from .debate import ClientDisconnectedError, DebateError, DebateManager
from .model_registry import available_model_payloads, available_models, provider_summaries
from .runtime_diary import runtime_diary
from .schemas import (
    ChatSession,
    DebateMessage,
    DebateRecord,
    RenameDebateRequest,
    RenameSessionRequest,
    SessionSettingsUpdate,
)


db = Database(settings.database_path)
debate_manager = DebateManager(db)


async def safe_send_json(websocket: WebSocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except WebSocketDisconnect:
        return False
    except RuntimeError as exc:
        if "Cannot call \"send\" once a close message has been sent" in str(exc):
            return False
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    runtime_diary.record(
        "backend terminal",
        "startup",
        f"{settings.app_name} backend started. Database path: {settings.database_path}",
    )
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "database": str(settings.database_path),
        "active_debates": debate_manager.active_count,
    }


@app.get("/api/models")
def models() -> dict:
    configured = available_models()
    include_mock = settings.mock_llm and not configured
    unlocked_models = available_model_payloads(include_mock=include_mock)
    return {
        "models": unlocked_models,
        "providers": provider_summaries(),
        "available_model_count": len(unlocked_models),
        "real_available_model_count": len(configured),
        "minimum_debate_models": 1,
        "selection_required": True,
        "mock_mode": settings.mock_llm,
    }


@app.post("/api/runtime-diary")
def record_runtime_diary(payload: dict) -> dict:
    source = str(payload.get("source") or "frontend/browser")
    event = str(payload.get("event") or "event")
    detail = str(payload.get("detail") or "")
    session_id = str(payload.get("session_id") or "").strip() or None
    runtime_diary.record(source, event, detail, session_id=session_id)
    return {"ok": True}


@app.get("/api/sessions", response_model=list[ChatSession])
def list_sessions() -> list[dict]:
    return db.list_sessions()


@app.post("/api/sessions", response_model=ChatSession, status_code=201)
def create_session() -> dict:
    try:
        return db.create_session(settings.max_sessions)
    except ValueError as exc:
        if str(exc) == "SESSION_LIMIT":
            raise HTTPException(
                status_code=409,
                detail=f"Only {settings.max_sessions} chat sessions are allowed at a time.",
            ) from exc
        raise


@app.patch("/api/sessions/{session_id}", response_model=ChatSession)
def rename_session(session_id: str, payload: RenameSessionRequest) -> dict:
    try:
        session = db.rename_session(session_id, payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@app.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(session_id: str) -> None:
    if not db.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")


@app.post("/api/sessions/{session_id}/clear-history", status_code=204)
def clear_session_history(session_id: str) -> None:
    if not db.clear_visible_history(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")


@app.post("/api/sessions/{session_id}/clear-memory", status_code=204)
def clear_session_memory(session_id: str) -> None:
    if not db.clear_memory(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")


@app.get("/api/sessions/{session_id}/messages", response_model=list[DebateMessage])
def list_messages(session_id: str) -> list[dict]:
    if not db.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")
    return db.list_messages(session_id)


@app.get("/api/sessions/{session_id}/debates", response_model=list[DebateRecord])
def list_debates(session_id: str) -> list[dict]:
    if not db.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")
    return db.list_debates(session_id)


@app.patch("/api/sessions/{session_id}/debates/{debate_id}", response_model=DebateRecord)
def rename_debate(session_id: str, debate_id: str, payload: RenameDebateRequest) -> dict:
    try:
        debate = db.rename_debate(session_id, debate_id, payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found.")
    return debate


@app.delete("/api/sessions/{session_id}/debates/{debate_id}", status_code=204)
def delete_debate_statistics(session_id: str, debate_id: str) -> None:
    if not db.hide_debate_statistics(session_id, debate_id):
        raise HTTPException(status_code=404, detail="Debate not found.")


@app.get("/api/sessions/{session_id}/settings")
def get_settings(session_id: str) -> dict:
    session_settings = db.get_session_settings(session_id)
    if not session_settings:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session_settings


@app.patch("/api/sessions/{session_id}/settings")
def update_settings(session_id: str, payload: SessionSettingsUpdate) -> dict:
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    session_settings = db.update_session_settings(session_id, updates)
    if not session_settings:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session_settings


@app.get("/api/sessions/{session_id}/analytics")
def session_analytics(
    session_id: str, debate_id: str | None = Query(default=None, alias="debate_id")
) -> dict:
    if not db.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")
    debates = db.list_debates(session_id)
    if not debates:
        return analyze_debate("", [])

    all_messages = db.list_messages(session_id)
    latest_debate = None
    debater_source: list[dict] = []
    ignored_roles = {"user", "assistant", "judge", "judge_assistant"}

    candidate_debates = debates
    if debate_id:
        selected_debate = db.get_debate(session_id, debate_id)
        if not selected_debate:
            raise HTTPException(status_code=404, detail="Debate not found.")
        candidate_debates = [selected_debate]

    for debate in candidate_debates:
        debate_messages = [
            message for message in all_messages if message["debate_id"] == debate["id"]
        ]
        debate_debaters = [
            message for message in debate_messages if message["role"] not in ignored_roles
        ]
        if debate_debaters:
            latest_debate = debate
            debater_source = debate_debaters
            break

    if latest_debate is None:
        analysis = analyze_debate("", [])
        analysis["source"] = {
            "mode": "selected_debate" if debate_id else "latest_debate",
            "debate_id": candidate_debates[0]["id"] if candidate_debates else "",
            "name": candidate_debates[0]["name"] if candidate_debates else "",
            "default_index": candidate_debates[0]["default_index"] if candidate_debates else 0,
            "topic": candidate_debates[0]["topic"] if candidate_debates else "",
            "debate_count": len(debates),
        }
        return analysis

    active_role_count = len({message["role"] for message in debater_source}) or 1
    debater_messages = [
        {
            "speaker": message["speaker"],
            "role": message["role"],
            "round": (index // active_role_count) + 1,
            "model": message["model"],
            "content": message["content"],
        }
        for index, message in enumerate(debater_source)
    ]
    topic = str(latest_debate.get("topic") or "")
    analysis = analyze_debate(topic, debater_messages)
    analysis["source"] = {
        "mode": "selected_debate" if debate_id else "latest_debate",
        "debate_id": latest_debate["id"],
        "name": latest_debate["name"],
        "default_index": latest_debate["default_index"],
        "topic": topic,
        "debate_count": len(debates),
    }
    return analysis


@app.websocket("/ws/debates/{session_id}")
async def debate_socket(websocket: WebSocket, session_id: str):
    await websocket.accept()

    if not db.get_session(session_id):
        await safe_send_json(websocket, {"type": "error", "message": "Session not found."})
        await websocket.close(code=1008)
        return

    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") not in {"start_debate", "start_interaction"}:
                if not await safe_send_json(
                    websocket,
                    {"type": "error", "message": "Unknown WebSocket event type."}
                ):
                    return
                continue

            topic = str(payload.get("topic", "")).strip()
            selected_model = str(payload.get("model", "")).strip()
            try:
                await debate_manager.run_interaction(websocket, session_id, topic, selected_model)
            except ClientDisconnectedError:
                return
            except DebateError as exc:
                if not await safe_send_json(websocket, {"type": "error", "message": str(exc)}):
                    return
            except WebSocketDisconnect:
                raise
            except Exception as exc:
                if not await safe_send_json(
                    websocket,
                    {"type": "error", "message": f"Debate failed: {exc}"},
                ):
                    return
    except WebSocketDisconnect:
        return
