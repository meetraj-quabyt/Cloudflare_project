from app.core.security import hash_token, utc_now
from app.repositories.db import Database


async def create_share_link(db: Database, link_id, file_id, token, expires_at=None, max_downloads=None) -> dict | None:
    th = hash_token(token)
    now = utc_now()
    await db.execute(
        """INSERT INTO share_links (id, file_id, token_hash, created_at, expires_at, max_downloads, download_count, is_active)
           VALUES (?,?,?,?,?,?,0,1)""",
        (link_id, file_id, th, now, expires_at, max_downloads),
    )
    return await get_by_id(db, link_id)


async def get_by_id(db: Database, link_id) -> dict | None:
    return await db.fetch_one("SELECT * FROM share_links WHERE id = ?", (link_id,))


async def get_by_token_hash(db: Database, token_hash) -> dict | None:
    return await db.fetch_one("SELECT * FROM share_links WHERE token_hash = ?", (token_hash,))


async def find_active_for_file(db: Database, file_id) -> dict | None:
    return await db.fetch_one(
        "SELECT * FROM share_links WHERE file_id = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1",
        (file_id,),
    )


async def list_for_file(db: Database, file_id) -> list[dict]:
    return await db.fetch_all("SELECT * FROM share_links WHERE file_id = ? ORDER BY created_at DESC", (file_id,))


async def revoke(db: Database, link_id):
    await db.execute("UPDATE share_links SET is_active = 0, revoked_at = ? WHERE id = ?", (utc_now(), link_id))


async def increment_download_count(db: Database, link_id):
    await db.execute("UPDATE share_links SET download_count = download_count + 1 WHERE id = ?", (link_id,))


async def list_all_active(db: Database):
    return await db.fetch_all("SELECT * FROM share_links WHERE is_active = 1")