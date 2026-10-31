from datetime import UTC, datetime
from typing import Any
from app.repositories.db import Database


async def list_sessions(db: Database) -> list[dict[str, Any]]:
    sql = "SELECT id, title, system_prompt, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC"
    return await db.fetch_all(sql)


async def create_session(db: Database, session_id: str, title: str, system_prompt: str = "") -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    sql = """
        INSERT INTO chat_sessions (id, title, system_prompt, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """
    await db.execute(sql, (session_id, title, system_prompt, now, now))
    return {
        "id": session_id,
        "title": title,
        "system_prompt": system_prompt,
        "created_at": now,
        "updated_at": now,
    }


async def get_session(db: Database, session_id: str) -> dict[str, Any] | None:
    sql = "SELECT id, title, system_prompt, created_at, updated_at FROM chat_sessions WHERE id = ?"
    return await db.fetch_one(sql, (session_id,))


async def delete_session(db: Database, session_id: str) -> None:
    await db.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    await db.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))


async def update_session_title(db: Database, session_id: str, title: str) -> None:
    now = datetime.now(UTC).isoformat()
    await db.execute("UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?", (title, now, session_id))


async def touch_session(db: Database, session_id: str) -> None:
    now = datetime.now(UTC).isoformat()
    await db.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (now, session_id))


async def get_messages(db: Database, session_id: str) -> list[dict[str, Any]]:
    sql = """
        SELECT id, session_id, role, content, tokens_used, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY created_at ASC
    """
    return await db.fetch_all(sql, (session_id,))


async def add_message(
    db: Database,
    message_id: str,
    session_id: str,
    role: str,
    content: str,
    tokens_used: int = 0,
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    sql = """
        INSERT INTO chat_messages (id, session_id, role, content, tokens_used, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    await db.execute(sql, (message_id, session_id, role, content, tokens_used, now))
    await touch_session(db, session_id)
    return {
        "id": message_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "tokens_used": tokens_used,
        "created_at": now,
    }

