import os
from datetime import UTC

from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.core.security import (
    is_allowed_content_type,
    is_expired,
    new_id,
    new_token,
    sanitize_filename,
    utc_future,
)
from app.models.schemas import (
    CompleteUploadRequest,
    InitiateUploadRequest,
    InitiateUploadResponse,
    UploadStatusResponse,
)
from app.repositories import event_repo, files_repo, session_repo, share_repo
from app.services.rate_limit import allow
from app.storage import get_storage

router = APIRouter(prefix="/uploads", tags=["uploads"])


def get_db(request: Request):
    return request.app.state.db


def get_storage_client(request: Request):
    storage = request.app.state.storage
    if storage is None:
        storage = get_storage()
    return storage


def get_owner(request: Request, body_owner=None):
    # Anonymous ownership: header or body
    owner = request.headers.get(settings.anonymous_owner_header)
    if not owner and body_owner:
        owner = body_owner
    if not owner:
        owner = request.client.host if request.client else "anonymous"
    return owner


@router.post("/initiate", response_model=InitiateUploadResponse)
async def initiate_upload(payload: InitiateUploadRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not allow(f"upload:{client_ip}", limit=settings.rate_limit_per_minute, window=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    if payload.size_bytes <= 0 or payload.size_bytes > settings.max_file_size_bytes:
        raise HTTPException(status_code=400, detail="Invalid file size")
    filename = sanitize_filename(payload.filename)
    ct = payload.content_type.split(";")[0].strip().lower()
    if not is_allowed_content_type(ct):
        raise HTTPException(status_code=400, detail="Unsupported content type")

    db = get_db(request)
    owner = get_owner(request, payload.owner_token)
    storage = get_storage_client(request)

    file_id = new_id("file")
    session_id = new_id("upl")
    object_key = f"uploads/{new_id()}/{filename}"

    await files_repo.create_file(db, file_id, filename, object_key, ct, payload.size_bytes, payload.checksum_sha256, owner)
    await session_repo.create_upload_session(db, session_id, file_id, payload.size_bytes, settings.upload_session_ttl_minutes)

    expires = settings.upload_url_ttl_seconds
    upload_url = storage.presign_upload(object_key, session_id=session_id, expires=expires)
    upload_method = "POST" if storage.is_local() else "PUT"
    await event_repo.record_event(db, new_id("evt"), file_id, "upload_initiated", "pending", upload_session_id=session_id,
                                 bytes_transferred=payload.size_bytes, metadata={"filename": filename})

    await session_repo.update_upload_session(db, session_id, "uploading")

    return InitiateUploadResponse(
        session_id=session_id,
        file_id=file_id,
        upload_url=upload_url,
        upload_method=upload_method,
        required_headers={"Content-Type": ct},
        expires_at=utc_future(seconds=expires),
    )


@router.post("/{session_id}/complete")
async def complete_upload(session_id: str, payload: CompleteUploadRequest, request: Request):
    db = get_db(request)
    storage = get_storage_client(request)
    session = await session_repo.get_upload_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if is_expired(session["expires_at"]):
        await session_repo.update_upload_session(db, session_id, "expired", failure_reason="expired")
        raise HTTPException(status_code=410, detail="Upload session expired")

    file_row = await files_repo.get_file(db, session["file_id"])
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    # Idempotent: already completed
    if session["status"] == "completed" or file_row["upload_status"] == "completed":
        # ensure share link exists
        link = await share_repo.find_active_for_file(db, file_row["id"])
        share_url = None
        if link:
            # cannot reconstruct raw token; return marker
            share_url = "/s/<token-already-issued>"
        return {"status": "completed", "file_id": file_row["id"], "share_url": share_url, "idempotent": True}

    # Verify object in storage
    meta = await storage.head_object(file_row["object_key"])
    if not meta:
        await session_repo.update_upload_session(db, session_id, "failed", failure_reason="object_missing")
        await event_repo.record_event(db, new_id("evt"), file_row["id"], "upload_failed", "failed", upload_session_id=session_id, metadata={"reason": "object_missing"})
        await files_repo.update_file_status(db, file_row["id"], "failed")
        raise HTTPException(status_code=400, detail="Uploaded object not found in storage")

    actual_size = meta.get("size")
    expected = session["expected_size_bytes"]
    if actual_size is not None and actual_size != expected:
        await session_repo.update_upload_session(db, session_id, "failed", actual_size=actual_size, failure_reason="size_mismatch")
        await event_repo.record_event(db, new_id("evt"), file_row["id"], "upload_failed", "failed", upload_session_id=session_id, metadata={"reason": "size_mismatch"})
        await files_repo.update_file_status(db, file_row["id"], "failed")
        raise HTTPException(status_code=400, detail="Uploaded file size does not match")

    # checksum verification if provided and storage returns etag (not reliable) -> skip strict; record
    checksum = payload.checksum_sha256 or file_row.get("checksum_sha256")
    from app.core.security import utc_now as _utc_now
    await files_repo.update_file_status(db, file_row["id"], "completed", uploaded_at=_utc_now(), size_bytes=actual_size or expected, checksum=checksum)
    await session_repo.update_upload_session(db, session_id, "completed", actual_size=actual_size or expected, completed=True)
    await event_repo.record_event(db, new_id("evt"), file_row["id"], "upload_completed", "success", upload_session_id=session_id, bytes_transferred=actual_size or expected)

    # Create share link
    token = new_token()
    link_id = new_id("share")
    expires_at = None  # default no expiry? use default_share? We'll set based on settings default hours
    from datetime import datetime, timedelta
    expires_at = (datetime.now(UTC) + timedelta(hours=settings.default_share_expires_hours)).isoformat()
    await share_repo.create_share_link(db, link_id, file_row["id"], token, expires_at=expires_at, max_downloads=settings.default_max_downloads)
    await event_repo.record_event(db, new_id("evt"), file_row["id"], "link_created", "success", share_link_id=link_id)

    frontend_base = os.environ.get("FRONTEND_BASE_URL", "http://localhost:5173")
    share_url = f"{frontend_base}/s/{token}"
    # Store raw token? We return it now; not stored. Need to return token. But schema has share_url only. Include token in response extra.
    return {
        "status": "completed",
        "file_id": file_row["id"],
        "share_id": link_id,
        "share_token": token,
        "share_url": share_url,
        "expires_at": expires_at,
    }


@router.get("/{session_id}", response_model=UploadStatusResponse)
async def upload_status(session_id: str, request: Request):
    db = get_db(request)
    session = await session_repo.get_upload_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return UploadStatusResponse(
        session_id=session["id"],
        file_id=session["file_id"],
        status=session["status"],
        expected_size_bytes=session["expected_size_bytes"],
        actual_size_bytes=session.get("actual_size_bytes"),
        failure_reason=session.get("failure_reason"),
    )


@router.post("/{session_id}/local")
async def local_upload(session_id: str, request: Request):
    db = get_db(request)
    storage = get_storage_client(request)
    session = await session_repo.get_upload_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if is_expired(session["expires_at"]):
        raise HTTPException(status_code=410, detail="Upload session expired")
    file_row = await files_repo.get_file(db, session["file_id"])
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    if not storage.is_local():
        raise HTTPException(status_code=400, detail="Local uploads are disabled")
    body = await request.body()
    storage.store_bytes(file_row["object_key"], body)
    return {"status": "uploaded", "bytes": len(body)}