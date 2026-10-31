import os
import secrets
from datetime import UTC

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.config import settings
from app.core.security import new_id
from app.models.schemas import ShareCreateRequest, ShareCreateResponse
from app.repositories import event_repo, files_repo, share_repo
from app.storage import get_storage

router = APIRouter(prefix="/files", tags=["files"])


def get_db(request):
    return request.app.state.db


def get_storage_client(request):
    storage = request.app.state.storage
    if storage is None:
        storage = get_storage()
    return storage


def get_owner(request, body_owner=None):
    owner = request.headers.get(settings.anonymous_owner_header)
    if not owner and body_owner:
        owner = body_owner
    if not owner:
        owner = request.client.host if request.client else "anonymous"
    return owner


@router.get("")
async def list_files(request: Request, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), owner_token: str | None = None):
    db = get_db(request)
    owner = get_owner(request, owner_token)
    rows, total = await files_repo.list_files(db, owner, limit, offset)
    return {"items": rows, "total": total, "limit": limit, "offset": offset}


@router.get("/{file_id}")
async def file_details(file_id: str, request: Request, owner_token: str | None = None):
    db = get_db(request)
    row = await files_repo.get_file(db, file_id)
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    owner = get_owner(request, owner_token)
    if row.get("owner_token") != owner:
        raise HTTPException(status_code=403, detail="Forbidden")
    if row.get("deleted_at"):
        raise HTTPException(status_code=404, detail="File deleted")
    links = await share_repo.list_for_file(db, file_id)
    events = await event_repo.list_events(db, file_id=file_id, limit=20)
    return {"file": row, "share_links": links, "recent_events": events}


@router.post("/{file_id}/share", response_model=ShareCreateResponse)
async def create_share(file_id: str, payload: ShareCreateRequest, request: Request):
    db = get_db(request)
    row = await files_repo.get_file(db, file_id)
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    owner = get_owner(request, payload.owner_token)
    if row.get("owner_token") != owner:
        raise HTTPException(status_code=403, detail="Forbidden")
    if row["upload_status"] != "completed":
        raise HTTPException(status_code=400, detail="File not ready")

    # rotate: revoke existing active links
    existing = await share_repo.list_for_file(db, file_id)
    for l in existing:
        if l.get("is_active"):
            await share_repo.revoke(db, l["id"])
            await event_repo.record_event(db, new_id("evt"), file_id, "link_revoked", "success", share_link_id=l["id"])

    token = secrets.token_urlsafe(32)
    link_id = new_id("share")
    expires_at = None
    if payload.expires_in_hours:
        from datetime import datetime, timedelta
        expires_at = (datetime.now(UTC) + timedelta(hours=payload.expires_in_hours)).isoformat()
    else:
        from datetime import datetime, timedelta
        expires_at = (datetime.now(UTC) + timedelta(hours=settings.default_share_expires_hours)).isoformat()
    max_dl = payload.max_downloads if payload.max_downloads is not None else settings.default_max_downloads
    await share_repo.create_share_link(db, link_id, file_id, token, expires_at=expires_at, max_downloads=max_dl)
    await event_repo.record_event(db, new_id("evt"), file_id, "link_created", "success", share_link_id=link_id)

    frontend_base = os.environ.get("FRONTEND_BASE_URL", "http://localhost:5173")
    share_url = f"{frontend_base}/s/{token}"
    return ShareCreateResponse(share_id=link_id, share_url=share_url, expires_at=expires_at, max_downloads=max_dl)


@router.delete("/{file_id}")
async def delete_file(file_id: str, request: Request, owner_token: str | None = None):
    db = get_db(request)
    storage = get_storage_client(request)
    row = await files_repo.get_file(db, file_id)
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    owner = get_owner(request, owner_token)
    if row.get("owner_token") != owner:
        raise HTTPException(status_code=403, detail="Forbidden")

    # revoke links
    links = await share_repo.list_for_file(db, file_id)
    for l in links:
        if l.get("is_active"):
            await share_repo.revoke(db, l["id"])
            await event_repo.record_event(db, new_id("evt"), file_id, "link_revoked", "success", share_link_id=l["id"])

    # delete storage object
    try:
        await storage.delete_object(row["object_key"])
    except Exception as exc:  # noqa: BLE001
        from app.core.logging import get_logger

        get_logger("files").warning("r2_delete_failed", error=str(exc))

    await files_repo.soft_delete_file(db, file_id)
    await event_repo.record_event(db, new_id("evt"), file_id, "file_deleted", "success")
    return {"status": "deleted", "file_id": file_id}


@router.get("/{file_id}/download")
async def download_file(file_id: str, request: Request):
    storage = get_storage_client(request)
    row = await files_repo.get_file(get_db(request), file_id)
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    if row.get("deleted_at") or row["upload_status"] != "completed":
        raise HTTPException(status_code=404, detail="File not available")
    if not storage.is_local():
        raise HTTPException(status_code=400, detail="Direct download only available in local mode")
    import io

    from fastapi.responses import StreamingResponse
    data = storage.read_bytes(row["object_key"])
    return StreamingResponse(io.BytesIO(data), media_type=row["content_type"], headers={"Content-Disposition": f'attachment; filename="{row["original_filename"]}"'})