from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Iterator
from uuid import uuid4


SESSION_COUNTER_KEY = "session_counter"
DEFAULT_SESSION_PREFIX = "Debate Session #"
DEFAULT_DEBATE_PREFIX = "Debate #"
AGENT_ROLE_KEYS = (
    "council_assistant",
    "lead_advocate",
    "rebuttal_critic",
    "evidence_researcher",
    "cross_examiner",
    "judge_assistant",
    "judge",
)
DEFAULT_AGENT_SETTINGS = {
    role: {
        "model": "",
        "temperature": 0.55,
        "max_tokens": 700,
        "response_length": "Normal",
        "web_search": False,
        "always_on": False,
    }
    for role in AGENT_ROLE_KEYS
}
DEFAULT_SESSION_SETTINGS = {
    "overall_model": "",
    "debaters_per_team": 3,
    "judge_assistant_enabled": True,
    "agent_settings": DEFAULT_AGENT_SETTINGS,
    "role_models": {
        "advocate": "",
        "critic": "",
        "researcher": "",
        "devils_advocate": "",
        "judge": "",
    },
    "temperature": 0.55,
    "max_tokens": 700,
    "debate_tone": "Academic",
    "language": "English",
    "response_length": "Normal",
    "auto_scroll": True,
    "show_timestamps": False,
    "show_token_count": False,
    "context_window": 2,
    "debate_rounds": 2,
    "researcher_web_search": False,
    "fact_check_mode": False,
    "export_format": "Markdown",
    "auto_save_interval": 30,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.lock = RLock()

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init(self) -> None:
        with self.lock, self.session() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS app_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    default_index INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS session_settings (
                    session_id TEXT PRIMARY KEY,
                    overall_model TEXT NOT NULL DEFAULT '',
                    debaters_per_team INTEGER NOT NULL DEFAULT 3,
                    judge_assistant_enabled INTEGER NOT NULL DEFAULT 1,
                    agent_settings TEXT NOT NULL DEFAULT '{}',
                    role_models TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    max_tokens INTEGER NOT NULL,
                    debate_tone TEXT NOT NULL,
                    language TEXT NOT NULL,
                    response_length TEXT NOT NULL,
                    auto_scroll INTEGER NOT NULL,
                    show_timestamps INTEGER NOT NULL,
                    show_token_count INTEGER NOT NULL,
                    context_window INTEGER NOT NULL,
                    debate_rounds INTEGER NOT NULL,
                    researcher_web_search INTEGER NOT NULL,
                    fact_check_mode INTEGER NOT NULL,
                    export_format TEXT NOT NULL,
                    auto_save_interval INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS debates (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    name TEXT NOT NULL DEFAULT '',
                    default_index INTEGER NOT NULL DEFAULT 0,
                    mode TEXT NOT NULL DEFAULT 'debate',
                    topic TEXT NOT NULL,
                    status TEXT NOT NULL,
                    judge_summary TEXT,
                    error TEXT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    hidden_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    debate_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    speaker TEXT NOT NULL,
                    model TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    hidden_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY(debate_id) REFERENCES debates(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session_sequence
                    ON messages(session_id, sequence);
                CREATE INDEX IF NOT EXISTS idx_debates_session_started
                    ON debates(session_id, started_at);
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO app_metadata (key, value)
                VALUES (?, '0')
                """,
                (SESSION_COUNTER_KEY,),
            )
            connection.execute(
                """
                UPDATE app_metadata
                SET value = (
                    SELECT CAST(COALESCE(MAX(default_index), 0) AS TEXT)
                    FROM sessions
                )
                WHERE key = ?
                  AND CAST(value AS INTEGER) < (
                    SELECT COALESCE(MAX(default_index), 0)
                    FROM sessions
                  )
                """,
                (SESSION_COUNTER_KEY,),
            )
            self._ensure_settings_schema(connection)
            self._ensure_history_schema(connection)
            rows = connection.execute("SELECT id FROM sessions").fetchall()
            for row in rows:
                self._ensure_settings(connection, row["id"])

    def _ensure_settings_schema(self, connection: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(session_settings)").fetchall()
        }
        if "overall_model" not in columns:
            connection.execute(
                "ALTER TABLE session_settings ADD COLUMN overall_model TEXT NOT NULL DEFAULT ''"
            )
        if "debaters_per_team" not in columns:
            connection.execute(
                "ALTER TABLE session_settings ADD COLUMN debaters_per_team INTEGER NOT NULL DEFAULT 3"
            )
        if "judge_assistant_enabled" not in columns:
            connection.execute(
                "ALTER TABLE session_settings ADD COLUMN judge_assistant_enabled INTEGER NOT NULL DEFAULT 1"
            )
        if "agent_settings" not in columns:
            connection.execute(
                "ALTER TABLE session_settings ADD COLUMN agent_settings TEXT NOT NULL DEFAULT '{}'"
            )

    def _ensure_history_schema(self, connection: sqlite3.Connection) -> None:
        debate_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(debates)").fetchall()
        }
        if "hidden_at" not in debate_columns:
            connection.execute("ALTER TABLE debates ADD COLUMN hidden_at TEXT")
        if "name" not in debate_columns:
            connection.execute("ALTER TABLE debates ADD COLUMN name TEXT NOT NULL DEFAULT ''")
        if "default_index" not in debate_columns:
            connection.execute(
                "ALTER TABLE debates ADD COLUMN default_index INTEGER NOT NULL DEFAULT 0"
            )
        if "mode" not in debate_columns:
            connection.execute("ALTER TABLE debates ADD COLUMN mode TEXT NOT NULL DEFAULT ''")

        debate_rows = connection.execute(
            "SELECT id, session_id, started_at FROM debates ORDER BY session_id, started_at ASC"
        ).fetchall()
        index_by_session: dict[str, int] = {}
        ignored_roles = ("user", "assistant", "judge", "judge_assistant")
        for row in debate_rows:
            session_id = row["session_id"]
            index_by_session[session_id] = index_by_session.get(session_id, 0) + 1
            debate_index = index_by_session[session_id]
            debater_count = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM messages
                WHERE debate_id = ?
                  AND role NOT IN ({",".join("?" for _ in ignored_roles)})
                """,
                (row["id"], *ignored_roles),
            ).fetchone()["total"]
            connection.execute(
                """
                UPDATE debates
                SET name = CASE WHEN name = '' THEN ? ELSE name END,
                    default_index = CASE WHEN default_index = 0 THEN ? ELSE default_index END,
                    mode = CASE
                        WHEN mode = '' THEN ?
                        ELSE mode
                    END
                WHERE id = ?
                """,
                (
                    f"{DEFAULT_DEBATE_PREFIX}{debate_index}",
                    debate_index,
                    "debate" if debater_count > 0 else "chat",
                    row["id"],
                ),
            )

        message_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(messages)").fetchall()
        }
        if "hidden_at" not in message_columns:
            connection.execute("ALTER TABLE messages ADD COLUMN hidden_at TEXT")

    def list_sessions(self) -> list[dict]:
        with self.lock, self.session() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM sessions
                ORDER BY updated_at DESC, created_at DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_session(self, session_id: str) -> dict | None:
        with self.lock, self.session() as connection:
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            return row_to_dict(row)

    def create_session(self, max_sessions: int) -> dict:
        with self.lock, self.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            session_count = connection.execute(
                "SELECT COUNT(*) AS total FROM sessions"
            ).fetchone()["total"]
            if session_count >= max_sessions:
                raise ValueError("SESSION_LIMIT")

            # Monotonic while any chat exists; reset only after the last chat is deleted.
            if session_count == 0:
                counter = 0
            else:
                counter = int(
                    connection.execute(
                        "SELECT value FROM app_metadata WHERE key = ?",
                        (SESSION_COUNTER_KEY,),
                    ).fetchone()["value"]
                )

            counter += 1
            now = utc_now()
            session_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO sessions (id, name, default_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, f"{DEFAULT_SESSION_PREFIX}{counter}", counter, now, now),
            )
            connection.execute(
                """
                INSERT INTO app_metadata (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (SESSION_COUNTER_KEY, str(counter)),
            )
            self._ensure_settings(connection, session_id)
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            return row_to_dict(row) or {}

    def _ensure_settings(self, connection: sqlite3.Connection, session_id: str) -> None:
        now = utc_now()
        connection.execute(
            """
            INSERT OR IGNORE INTO session_settings (
                session_id,
                overall_model,
                debaters_per_team,
                judge_assistant_enabled,
                agent_settings,
                role_models,
                temperature,
                max_tokens,
                debate_tone,
                language,
                response_length,
                auto_scroll,
                show_timestamps,
                show_token_count,
                context_window,
                debate_rounds,
                researcher_web_search,
                fact_check_mode,
                export_format,
                auto_save_interval,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                DEFAULT_SESSION_SETTINGS["overall_model"],
                DEFAULT_SESSION_SETTINGS["debaters_per_team"],
                int(DEFAULT_SESSION_SETTINGS["judge_assistant_enabled"]),
                json.dumps(DEFAULT_SESSION_SETTINGS["agent_settings"]),
                json.dumps(DEFAULT_SESSION_SETTINGS["role_models"]),
                DEFAULT_SESSION_SETTINGS["temperature"],
                DEFAULT_SESSION_SETTINGS["max_tokens"],
                DEFAULT_SESSION_SETTINGS["debate_tone"],
                DEFAULT_SESSION_SETTINGS["language"],
                DEFAULT_SESSION_SETTINGS["response_length"],
                int(DEFAULT_SESSION_SETTINGS["auto_scroll"]),
                int(DEFAULT_SESSION_SETTINGS["show_timestamps"]),
                int(DEFAULT_SESSION_SETTINGS["show_token_count"]),
                DEFAULT_SESSION_SETTINGS["context_window"],
                DEFAULT_SESSION_SETTINGS["debate_rounds"],
                int(DEFAULT_SESSION_SETTINGS["researcher_web_search"]),
                int(DEFAULT_SESSION_SETTINGS["fact_check_mode"]),
                DEFAULT_SESSION_SETTINGS["export_format"],
                DEFAULT_SESSION_SETTINGS["auto_save_interval"],
                now,
            ),
        )

    def get_session_settings(self, session_id: str) -> dict | None:
        with self.lock, self.session() as connection:
            if not self.get_session(session_id):
                return None
            self._ensure_settings(connection, session_id)
            row = connection.execute(
                "SELECT * FROM session_settings WHERE session_id = ?", (session_id,)
            ).fetchone()
            return self._settings_row_to_dict(row)

    def update_session_settings(self, session_id: str, updates: dict) -> dict | None:
        allowed = set(DEFAULT_SESSION_SETTINGS)
        cleaned = {key: value for key, value in updates.items() if key in allowed}
        if not cleaned:
            return self.get_session_settings(session_id)

        with self.lock, self.session() as connection:
            if not connection.execute(
                "SELECT id FROM sessions WHERE id = ?", (session_id,)
            ).fetchone():
                return None
            self._ensure_settings(connection, session_id)
            current = self._settings_row_to_dict(
                connection.execute(
                    "SELECT * FROM session_settings WHERE session_id = ?", (session_id,)
                ).fetchone()
            )
            next_settings = self._normalize_settings({**(current or {}), **cleaned})
            connection.execute(
                """
                UPDATE session_settings
                SET overall_model = ?,
                    debaters_per_team = ?,
                    judge_assistant_enabled = ?,
                    agent_settings = ?,
                    role_models = ?,
                    temperature = ?,
                    max_tokens = ?,
                    debate_tone = ?,
                    language = ?,
                    response_length = ?,
                    auto_scroll = ?,
                    show_timestamps = ?,
                    show_token_count = ?,
                    context_window = ?,
                    debate_rounds = ?,
                    researcher_web_search = ?,
                    fact_check_mode = ?,
                    export_format = ?,
                    auto_save_interval = ?,
                    updated_at = ?
                WHERE session_id = ?
                """,
                (
                    next_settings["overall_model"],
                    next_settings["debaters_per_team"],
                    int(next_settings["judge_assistant_enabled"]),
                    json.dumps(next_settings["agent_settings"]),
                    json.dumps(next_settings["role_models"]),
                    next_settings["temperature"],
                    next_settings["max_tokens"],
                    next_settings["debate_tone"],
                    next_settings["language"],
                    next_settings["response_length"],
                    int(next_settings["auto_scroll"]),
                    int(next_settings["show_timestamps"]),
                    int(next_settings["show_token_count"]),
                    next_settings["context_window"],
                    next_settings["debate_rounds"],
                    int(next_settings["researcher_web_search"]),
                    int(next_settings["fact_check_mode"]),
                    next_settings["export_format"],
                    next_settings["auto_save_interval"],
                    utc_now(),
                    session_id,
                ),
            )
            return next_settings

    def _settings_row_to_dict(self, row: sqlite3.Row | None) -> dict | None:
        if not row:
            return None
        return self._normalize_settings(
            {
                "role_models": json.loads(row["role_models"] or "{}"),
                "overall_model": row["overall_model"],
                "debaters_per_team": row["debaters_per_team"],
                "judge_assistant_enabled": bool(row["judge_assistant_enabled"]),
                "agent_settings": json.loads(row["agent_settings"] or "{}"),
                "temperature": row["temperature"],
                "max_tokens": row["max_tokens"],
                "debate_tone": row["debate_tone"],
                "language": row["language"],
                "response_length": row["response_length"],
                "auto_scroll": bool(row["auto_scroll"]),
                "show_timestamps": bool(row["show_timestamps"]),
                "show_token_count": bool(row["show_token_count"]),
                "context_window": row["context_window"],
                "debate_rounds": row["debate_rounds"],
                "researcher_web_search": bool(row["researcher_web_search"]),
                "fact_check_mode": bool(row["fact_check_mode"]),
                "export_format": row["export_format"],
                "auto_save_interval": row["auto_save_interval"],
                "updated_at": row["updated_at"],
            }
        )

    def _normalize_settings(self, settings_payload: dict) -> dict:
        merged = {**DEFAULT_SESSION_SETTINGS, **settings_payload}
        role_models = {**DEFAULT_SESSION_SETTINGS["role_models"], **(merged.get("role_models") or {})}
        agent_settings = self._normalize_agent_settings(
            merged.get("agent_settings") or {},
            role_models,
            merged,
        )
        return {
            "overall_model": str(merged.get("overall_model", "")).strip(),
            "debaters_per_team": max(1, min(4, int(merged.get("debaters_per_team", 3)))),
            "judge_assistant_enabled": bool(merged.get("judge_assistant_enabled", True)),
            "agent_settings": agent_settings,
            "role_models": {key: str(role_models.get(key, "")).strip() for key in DEFAULT_SESSION_SETTINGS["role_models"]},
            "temperature": max(0.0, min(1.0, float(merged.get("temperature", 0.55)))),
            "max_tokens": max(120, min(2000, int(merged.get("max_tokens", 700)))),
            "debate_tone": str(merged.get("debate_tone", "Academic")),
            "language": str(merged.get("language", "English")),
            "response_length": str(merged.get("response_length", "Normal")),
            "auto_scroll": bool(merged.get("auto_scroll", True)),
            "show_timestamps": bool(merged.get("show_timestamps", False)),
            "show_token_count": bool(merged.get("show_token_count", False)),
            "context_window": max(0, min(6, int(merged.get("context_window", 2)))),
            "debate_rounds": max(1, min(6, int(merged.get("debate_rounds", 2)))),
            "researcher_web_search": bool(merged.get("researcher_web_search", False)),
            "fact_check_mode": bool(merged.get("fact_check_mode", False)),
            "export_format": str(merged.get("export_format", "Markdown")),
            "auto_save_interval": max(5, min(300, int(merged.get("auto_save_interval", 30)))),
            "updated_at": str(merged.get("updated_at", utc_now())),
        }

    def _normalize_agent_settings(
        self,
        agent_payload: dict,
        legacy_role_models: dict,
        merged: dict,
    ) -> dict:
        legacy_model_map = {
            "lead_advocate": legacy_role_models.get("advocate", ""),
            "rebuttal_critic": legacy_role_models.get("critic", ""),
            "evidence_researcher": legacy_role_models.get("researcher", ""),
            "cross_examiner": legacy_role_models.get("devils_advocate", ""),
            "judge": legacy_role_models.get("judge", ""),
        }
        normalized = {}
        for role in AGENT_ROLE_KEYS:
            base = DEFAULT_AGENT_SETTINGS[role]
            raw = agent_payload.get(role, {}) if isinstance(agent_payload, dict) else {}
            if not isinstance(raw, dict):
                raw = {}
            model = str(raw.get("model", legacy_model_map.get(role, ""))).strip()
            normalized[role] = {
                "model": model,
                "temperature": max(0.0, min(1.0, float(raw.get("temperature", merged.get("temperature", base["temperature"]))))),
                "max_tokens": max(120, min(2000, int(raw.get("max_tokens", merged.get("max_tokens", base["max_tokens"]))))),
                "response_length": self._normalize_choice(
                    raw.get("response_length", merged.get("response_length", base["response_length"])),
                    {"Concise", "Normal", "Detailed"},
                    "Normal",
                ),
                "web_search": bool(raw.get("web_search", merged.get("researcher_web_search", base["web_search"]))),
                "always_on": bool(raw.get("always_on", base["always_on"])),
            }
        return normalized

    def _normalize_choice(self, value: object, choices: set[str], default: str) -> str:
        cleaned = str(value)
        return cleaned if cleaned in choices else default

    def rename_session(self, session_id: str, name: str) -> dict | None:
        cleaned = " ".join(name.strip().split())
        if not cleaned:
            raise ValueError("EMPTY_NAME")
        if len(cleaned) > 80:
            raise ValueError("NAME_TOO_LONG")

        with self.lock, self.session() as connection:
            now = utc_now()
            cursor = connection.execute(
                """
                UPDATE sessions
                SET name = ?, updated_at = ?
                WHERE id = ?
                """,
                (cleaned, now, session_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            return row_to_dict(row)

    def delete_session(self, session_id: str) -> bool:
        with self.lock, self.session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            deleted = cursor.rowcount > 0
            remaining = connection.execute(
                "SELECT COUNT(*) AS total FROM sessions"
            ).fetchone()["total"]
            if remaining == 0:
                connection.execute(
                    "UPDATE app_metadata SET value = '0' WHERE key = ?",
                    (SESSION_COUNTER_KEY,),
                )
            return deleted

    def touch_session(self, session_id: str) -> None:
        with self.lock, self.session() as connection:
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (utc_now(), session_id),
            )

    def create_debate(self, session_id: str, topic: str, *, mode: str = "debate") -> dict:
        with self.lock, self.session() as connection:
            now = utc_now()
            debate_id = str(uuid4())
            visible_debate_count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM debates
                WHERE session_id = ?
                  AND mode = 'debate'
                  AND hidden_at IS NULL
                """,
                (session_id,),
            ).fetchone()["total"]
            if mode == "debate":
                if visible_debate_count == 0:
                    debate_index = 1
                else:
                    debate_index = (
                        connection.execute(
                            """
                            SELECT COALESCE(MAX(default_index), 0) + 1 AS next_index
                            FROM debates
                            WHERE session_id = ?
                              AND mode = 'debate'
                            """,
                            (session_id,),
                        ).fetchone()["next_index"]
                        or 1
                    )
                debate_name = f"{DEFAULT_DEBATE_PREFIX}{debate_index}"
            else:
                debate_index = 0
                debate_name = "Council Assistant Chat"
            connection.execute(
                """
                INSERT INTO debates
                    (id, session_id, name, default_index, mode, topic, status, started_at, hidden_at)
                VALUES (?, ?, ?, ?, ?, ?, 'running', ?, NULL)
                """,
                (debate_id, session_id, debate_name, debate_index, mode, topic, now),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id)
            )
            row = connection.execute(
                "SELECT * FROM debates WHERE id = ?", (debate_id,)
            ).fetchone()
            return row_to_dict(row) or {}

    def complete_debate(self, debate_id: str, judge_summary: str) -> None:
        with self.lock, self.session() as connection:
            connection.execute(
                """
                UPDATE debates
                SET status = 'completed', judge_summary = ?, finished_at = ?
                WHERE id = ?
                """,
                (judge_summary, utc_now(), debate_id),
            )

    def fail_debate(self, debate_id: str, error: str) -> None:
        with self.lock, self.session() as connection:
            connection.execute(
                """
                UPDATE debates
                SET status = 'failed', error = ?, finished_at = ?
                WHERE id = ?
                """,
                (error[:1000], utc_now(), debate_id),
            )

    def list_debates(self, session_id: str, *, include_hidden: bool = False) -> list[dict]:
        with self.lock, self.session() as connection:
            visibility_clause = "" if include_hidden else "AND hidden_at IS NULL"
            rows = connection.execute(
                f"""
                SELECT *
                FROM debates
                WHERE session_id = ?
                  AND mode = 'debate'
                  {visibility_clause}
                ORDER BY default_index DESC, started_at DESC
                """,
                (session_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_debate(
        self, session_id: str, debate_id: str, *, include_hidden: bool = False
    ) -> dict | None:
        with self.lock, self.session() as connection:
            visibility_clause = "" if include_hidden else "AND hidden_at IS NULL"
            row = connection.execute(
                f"""
                SELECT *
                FROM debates
                WHERE id = ?
                  AND session_id = ?
                  AND mode = 'debate'
                  {visibility_clause}
                """,
                (debate_id, session_id),
            ).fetchone()
            return row_to_dict(row)

    def rename_debate(self, session_id: str, debate_id: str, name: str) -> dict | None:
        cleaned = " ".join(name.strip().split())
        if not cleaned:
            raise ValueError("EMPTY_NAME")
        if len(cleaned) > 80:
            raise ValueError("NAME_TOO_LONG")

        with self.lock, self.session() as connection:
            cursor = connection.execute(
                """
                UPDATE debates
                SET name = ?
                WHERE id = ?
                  AND session_id = ?
                  AND mode = 'debate'
                  AND hidden_at IS NULL
                """,
                (cleaned, debate_id, session_id),
            )
            if cursor.rowcount == 0:
                return None
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?", (utc_now(), session_id)
            )
            row = connection.execute(
                "SELECT * FROM debates WHERE id = ? AND session_id = ?",
                (debate_id, session_id),
            ).fetchone()
            return row_to_dict(row)

    def hide_debate_statistics(self, session_id: str, debate_id: str) -> bool:
        with self.lock, self.session() as connection:
            now = utc_now()
            cursor = connection.execute(
                """
                UPDATE debates
                SET hidden_at = ?
                WHERE id = ?
                  AND session_id = ?
                  AND mode = 'debate'
                  AND hidden_at IS NULL
                """,
                (now, debate_id, session_id),
            )
            if cursor.rowcount == 0:
                return False
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id)
            )
            return True

    def add_message(
        self,
        *,
        session_id: str,
        debate_id: str,
        role: str,
        speaker: str,
        model: str,
        content: str,
    ) -> dict:
        with self.lock, self.session() as connection:
            sequence = (
                connection.execute(
                    """
                    SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence
                    FROM messages
                    WHERE session_id = ?
                    """,
                    (session_id,),
                ).fetchone()["next_sequence"]
                or 1
            )
            now = utc_now()
            message_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO messages
                    (id, session_id, debate_id, role, speaker, model, content, sequence, created_at, hidden_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    message_id,
                    session_id,
                    debate_id,
                    role,
                    speaker,
                    model,
                    content,
                    sequence,
                    now,
                ),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id)
            )
            row = connection.execute(
                "SELECT * FROM messages WHERE id = ?", (message_id,)
            ).fetchone()
            return row_to_dict(row) or {}

    def list_messages(self, session_id: str, *, include_hidden: bool = False) -> list[dict]:
        with self.lock, self.session() as connection:
            visibility_clause = "" if include_hidden else "AND hidden_at IS NULL"
            rows = connection.execute(
                f"""
                SELECT *
                FROM messages
                WHERE session_id = ?
                  {visibility_clause}
                ORDER BY sequence ASC
                """,
                (session_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def clear_visible_history(self, session_id: str) -> bool:
        with self.lock, self.session() as connection:
            if not connection.execute(
                "SELECT id FROM sessions WHERE id = ?", (session_id,)
            ).fetchone():
                return False

            now = utc_now()
            connection.execute(
                """
                UPDATE messages
                SET hidden_at = ?
                WHERE session_id = ?
                  AND hidden_at IS NULL
                """,
                (now, session_id),
            )
            connection.execute(
                """
                UPDATE debates
                SET hidden_at = ?
                WHERE session_id = ?
                  AND hidden_at IS NULL
                """,
                (now, session_id),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id)
            )
            return True

    def clear_memory(self, session_id: str) -> bool:
        with self.lock, self.session() as connection:
            if not connection.execute(
                "SELECT id FROM sessions WHERE id = ?", (session_id,)
            ).fetchone():
                return False

            now = utc_now()
            connection.execute("DELETE FROM debates WHERE session_id = ?", (session_id,))
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id)
            )
            return True
