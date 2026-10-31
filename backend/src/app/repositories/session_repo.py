from app.core.security import utc_future, utc_now
from app.repositories.db import Database


# Upload sessions
async def create_upload_session(db: Database, session_id, file_id, expected_size, expires_minutes=60) -> dict | None:
    now = utc_now()
    expires = utc_future(minutes=expires_minutes)
    await db.execute(
        """INSERT INTO upload_sessions (id, file_id, status, expected_size_bytes, created_at, expires_at)
           VALUES (?,?,?,?,?,?)""",
        (session_id, file_id, "pending", expected_size, now, expires),
    )
    return await get_upload_session(db, session_id)


async def get_upload_session(db: Database, session_id) -> dict | None:
    return await db.fetch_one("SELECT * FROM upload_sessions WHERE id = ?", (session_id,))


async def update_upload_session(db: Database, session_id, status, actual_size=None, failure_reason=None, completed=False):
    sets = ["status = ?"]
    params = [status]
    if actual_size is not None:
        sets.append("actual_size_bytes = ?")
        params.append(actual_size)
    if failure_reason is not None:
        sets.append("failure_reason = ?")
        params.append(failure_reason)
    if completed:
        sets.append("completed_at = ?")
        params.append(utc_now())
    params.append(session_id)
    await db.execute(f"UPDATE upload_sessions SET {', '.join(sets)} WHERE id = ?", tuple(params))


# Download sessions
async def create_download_session(db: Database, session_id, file_id, share_link_id) -> dict | None:
    now = utc_now()
    await db.execute(
        """INSERT INTO download_sessions (id, file_id, share_link_id, status, created_at)
           VALUES (?,?,?,?,?)""",
        (session_id, file_id, share_link_id, "initiated", now),
    )
    return await get_download_session(db, session_id)


async def get_download_session(db: Database, session_id) -> dict | None:
    return await db.fetch_one("SELECT * FROM download_sessions WHERE id = ?", (session_id,))


async def update_download_session(db: Database, session_id, status, url_issued=False, completed=False, bytes_transferred=None, failure_reason=None):
    sets = ["status = ?"]
    params = [status]
    if url_issued:
        sets.append("url_issued_at = ?")
        params.append(utc_now())
    if completed:
        sets.append("completed_at = ?")
        params.append(utc_now())
    if bytes_transferred is not None:
        sets.append("bytes_transferred = ?")
        params.append(bytes_transferred)
    if failure_reason is not None:
        sets.append("failure_reason = ?")
        params.append(failure_reason)
    params.append(session_id)
    await db.execute(f"UPDATE download_sessions SET {', '.join(sets)} WHERE id = ?", tuple(params))