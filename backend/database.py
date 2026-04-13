import aiosqlite
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "debate_council.db")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                session_number INTEGER NOT NULL,
                model TEXT NOT NULL DEFAULT 'gpt-4o',
                topic TEXT,
                status TEXT NOT NULL DEFAULT 'idle',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS session_counter (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                next_number INTEGER NOT NULL DEFAULT 1
            );

            INSERT OR IGNORE INTO session_counter (id, next_number) VALUES (1, 1);
        """)
        await db.commit()
    finally:
        await db.close()


async def get_next_session_number() -> int:
    db = await get_db()
    try:
        # Check if any sessions exist
        cursor = await db.execute("SELECT COUNT(*) as count FROM sessions")
        row = await cursor.fetchone()
        count = row[0]

        if count == 0:
            # Reset counter if all sessions deleted
            await db.execute("UPDATE session_counter SET next_number = 1 WHERE id = 1")
            await db.commit()

        cursor = await db.execute("SELECT next_number FROM session_counter WHERE id = 1")
        row = await cursor.fetchone()
        next_num = row[0]

        await db.execute("UPDATE session_counter SET next_number = ? WHERE id = 1", (next_num + 1,))
        await db.commit()
        return next_num
    finally:
        await db.close()
