from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.core.security import hash_token, is_expired, new_id, utc_future
from app.models.schemas import DownloadInitiateResponse, PublicShareInfo
from app.repositories import event_repo, files_repo, session_repo, share_repo
from app.services.rate_limit import allow
from app.storage import get_storage

router = APIRouter(prefix="/shares", tags=["shares"])


def get_db(request):
    return request.app.state.db


def get_owner(request):
    owner = request.headers.get(settings.anonymous_owner_header)
    if not owner:
        owner = request.client.host if request.client else "anonymous"
    return owner


@router.get("/{token}")
async def public_share_info(token: str, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not allow(f"sharelookup:{client_ip}", limit=settings.rate_limit_per_minute, window=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    db = get_db(request)
    th = hash_token(token)
    link = await share_repo.get_by_token_hash(db, th)
    if not link:
        raise HTTPException(status_code=404, detail="Invalid share link")
    if not link.get("is_active"):
        raise HTTPException(status_code=410, detail="Share link revoked")
    if is_expired(link.get("expires_at")):
        raise HTTPException(status_code=410, detail="Share link expired")

    file_row = await files_repo.get_file(db, link["file_id"])
    if not file_row or file_row.get("deleted_at"):
        raise HTTPException(status_code=404, detail="File not available")
    if file_row["upload_status"] != "completed":
        raise HTTPException(status_code=404, detail="File not available")

    remaining = None
    if link.get("max_downloads") is not None:
        remaining = max(0, link["max_downloads"] - link["download_count"])

    return PublicShareInfo(
        file_name=file_row["original_filename"],
        size_bytes=file_row["size_bytes"],
        content_type=file_row["content_type"],
        upload_date=file_row.get("uploaded_at") or file_row.get("created_at"),
        expires_at=link.get("expires_at"),
        remaining_downloads=remaining,
        is_active=bool(link.get("is_active")),
    )


@router.post("/{share_id}/revoke")
async def revoke_share(share_id: str, request: Request):
    db = get_db(request)
    link = await share_repo.get_by_id(db, share_id)
    if not link:
        raise HTTPException(status_code=404, detail="Share link not found")
    # ownership check via file
    file_row = await files_repo.get_file(db, link["file_id"])
    owner = get_owner(request)
    if file_row and file_row.get("owner_token") != owner:
        raise HTTPException(status_code=403, detail="Forbidden")
    await share_repo.revoke(db, share_id)
    await event_repo.record_event(db, new_id("evt"), link["file_id"], "link_revoked", "success", share_link_id=share_id)
    return {"status": "revoked", "share_id": share_id}


@router.post("/{token}/downloads")
async def initiate_download(token: str, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not allow(f"download:{client_ip}", limit=settings.rate_limit_per_minute, window=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    db = get_db(request)
    storage = request.app.state.storage
    if storage is None:
        storage = get_storage()

    th = hash_token(token)
    link = await share_repo.get_by_token_hash(db, th)
    if not link:
        raise HTTPException(status_code=404, detail="Invalid share link")
    if not link.get("is_active"):
        raise HTTPException(status_code=410, detail="Share link revoked")
    if is_expired(link.get("expires_at")):
        raise HTTPException(status_code=410, detail="Share link expired")

    file_row = await files_repo.get_file(db, link["file_id"])
    if not file_row or file_row.get("deleted_at") or file_row["upload_status"] != "completed":
        raise HTTPException(status_code=404, detail="File not available")

    # download limit check (successful-count based)
    if link.get("max_downloads") is not None and link["download_count"] >= link["max_downloads"]:
        raise HTTPException(status_code=429, detail="Download limit reached")

    session_id = new_id("dl")
    await session_repo.create_download_session(db, session_id, file_row["id"], link["id"])
    await event_repo.record_event(db, new_id("evt"), file_row["id"], "download_initiated", "initiated",
                                 share_link_id=link["id"], download_session_id=session_id)

    expires = settings.download_url_ttl_seconds
    download_url = storage.presign_download(file_row["object_key"], file_id=file_row["id"], expires=expires)
    await session_repo.update_download_session(db, session_id, "URL_issued", url_issued=True)
    await event_repo.record_event(db, new_id("evt"), file_row["id"], "download_url_issued", "success",
                                 share_link_id=link["id"], download_session_id=session_id)

    return DownloadInitiateResponse(
        download_session_id=session_id,
        download_url=download_url,
        expires_at=utc_future(seconds=expires),
        file_name=file_row["original_filename"],
        size_bytes=file_row["size_bytes"],
    )