from app.core.security import utc_now
from app.repositories.db import Database


async def create_file(db: Database, file_id, original_filename, object_key, content_type, size_bytes, checksum, owner_token) -> dict | None:
    now = utc_now()
    await db.execute(
        """INSERT INTO files (id, original_filename, object_key, content_type, size_bytes, checksum_sha256, upload_status, created_at, owner_token)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (file_id, original_filename, object_key, content_type, size_bytes, checksum, "pending", now, owner_token),
    )
    return await get_file(db, file_id)


async def get_file(db: Database, file_id) -> dict | None:
    return await db.fetch_one("SELECT * FROM files WHERE id = ?", (file_id,))


async def list_files(db: Database, owner_token: str, limit: int, offset: int) -> tuple[list[dict], int]:
    rows = await db.fetch_all(
        "SELECT * FROM files WHERE owner_token = ? AND deleted_at IS NULL ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (owner_token, limit, offset),
    )
    cnt = await db.fetch_one("SELECT COUNT(*) as c FROM files WHERE owner_token = ? AND deleted_at IS NULL", (owner_token,))
    total = cnt["c"] if cnt else 0
    return rows, total


async def update_file_status(db: Database, file_id, status, uploaded_at=None, size_bytes=None, checksum=None):
    sets = ["upload_status = ?"]
    params = [status]
    if uploaded_at is not None:
        sets.append("uploaded_at = ?")
        params.append(uploaded_at)
    if size_bytes is not None:
        sets.append("size_bytes = ?")
        params.append(size_bytes)
    if checksum is not None:
        sets.append("checksum_sha256 = ?")
        params.append(checksum)
    params.append(file_id)
    await db.execute(f"UPDATE files SET {', '.join(sets)} WHERE id = ?", tuple(params))


async def soft_delete_file(db: Database, file_id):
    await db.execute("UPDATE files SET deleted_at = ?, upload_status = 'expired' WHERE id = ?", (utc_now(), file_id))


async def storage_totals(db: Database, owner_token: str):
    row = await db.fetch_one(
        "SELECT COUNT(*) as c, COALESCE(SUM(size_bytes),0) as s FROM files WHERE owner_token = ? AND deleted_at IS NULL AND upload_status='completed'",
        (owner_token,),
    )
    downloads = await db.fetch_one(
        """SELECT COALESCE(SUM(sl.download_count),0) as d FROM share_links sl JOIN files f ON f.id=sl.file_id WHERE f.owner_token=?""",
        (owner_token,),
    )
    return {
        "files": row["c"] if row else 0,
        "storage_bytes": row["s"] if row else 0,
        "downloads": downloads["d"] if downloads else 0,
    }