import json

from app.core.security import utc_now
from app.repositories.db import Database


async def record_event(db: Database, event_id, file_id, event_type, status, share_link_id=None, upload_session_id=None, download_session_id=None, bytes_transferred=None, metadata=None):
    meta = json.dumps(metadata) if metadata is not None else None
    await db.execute(
        """INSERT INTO file_events (id, file_id, share_link_id, upload_session_id, download_session_id, event_type, status, occurred_at, bytes_transferred, metadata_json)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (event_id, file_id, share_link_id, upload_session_id, download_session_id, event_type, status, utc_now(), bytes_transferred, meta),
    )


async def list_events(db: Database, owner_token=None, file_id=None, event_type=None, limit=50, offset=0, since=None, until=None):
    where = []
    params = []
    # restrict to owner via files
    if owner_token is not None:
        where.append("f.owner_token = ?")
        params.append(owner_token)
    if file_id:
        where.append("fe.file_id = ?")
        params.append(file_id)
    if event_type:
        where.append("fe.event_type = ?")
        params.append(event_type)
    if since:
        where.append("fe.occurred_at >= ?")
        params.append(since)
    if until:
        where.append("fe.occurred_at <= ?")
        params.append(until)
    join = "JOIN files f ON f.id = fe.file_id" if owner_token is not None else ""
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""SELECT fe.* FROM file_events fe {join} {where_sql} ORDER BY fe.occurred_at DESC LIMIT ? OFFSET ?"""
    params.extend([limit, offset])
    return await db.fetch_all(sql, tuple(params))


async def count_events(db: Database, owner_token=None, file_id=None, event_type=None):
    where = []
    params = []
    if owner_token is not None:
        where.append("f.owner_token = ?")
        params.append(owner_token)
    if file_id:
        where.append("fe.file_id = ?")
        params.append(file_id)
    if event_type:
        where.append("fe.event_type = ?")
        params.append(event_type)
    join = "JOIN files f ON f.id = fe.file_id" if owner_token is not None else ""
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    row = await db.fetch_one(f"SELECT COUNT(*) as c FROM file_events fe {join} {where_sql}", tuple(params))
    return row["c"] if row else 0