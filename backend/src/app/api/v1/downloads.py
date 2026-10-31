from fastapi import APIRouter, HTTPException, Request

from app.core.security import is_expired, new_id
from app.models.schemas import (
    CompleteDownloadRequest,
    FailDownloadRequest,
)
from app.repositories import event_repo, files_repo, session_repo, share_repo

router = APIRouter(prefix="/downloads", tags=["downloads"])
# share-scoped download init is under /shares/{token}/downloads, handled in shares router? We'll add here with separate router in main? Instead add endpoint in this file with prefix override via include. We'll register a separate router.

# We'll implement download init in shares.py to match path /shares/{token}/downloads.
# But keep completion/fail here.

def get_db(request):
    return request.app.state.db


def get_r2(request):
    return request.app.state.r2


@router.post("/{session_id}/complete")
async def complete_download(session_id: str, payload: CompleteDownloadRequest, request: Request):
    db = get_db(request)
    session = await session_repo.get_download_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if is_expired(session.get("created_at")) and session["status"] not in ("client_reported_complete",):
        # expiry check on created+ttl; use created_at + download_session_ttl
        pass

    # Idempotent
    if session["status"] == "client_reported_complete":
        return {"status": "client_reported_complete", "idempotent": True}

    if session["status"] in ("failed", "expired"):
        raise HTTPException(status_code=400, detail="Session not active")

    file_row = await files_repo.get_file(db, session["file_id"])
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    # validate bytes
    bytes_transferred = payload.bytes_transferred
    evidence = "client_reported"
    if bytes_transferred is not None and file_row.get("size_bytes") and bytes_transferred != file_row["size_bytes"]:
        evidence = "client_reported_mismatch"

    await session_repo.update_download_session(db, session_id, "client_reported_complete", completed=True, bytes_transferred=bytes_transferred)
    await event_repo.record_event(
        db, new_id("evt"), session["file_id"], "download_client_reported_complete", "client_reported",
        share_link_id=session["share_link_id"], download_session_id=session_id,
        bytes_transferred=bytes_transferred, metadata={"evidence": evidence, "source": "browser"},
    )

    # Increment successful download counter only on first client-reported completion
    link = await share_repo.get_by_id(db, session["share_link_id"])
    if link:
        await share_repo.increment_download_count(db, session["share_link_id"])

    return {"status": "client_reported_complete", "evidence": evidence}


@router.post("/{session_id}/fail")
async def fail_download(session_id: str, payload: FailDownloadRequest, request: Request):
    db = get_db(request)
    session = await session_repo.get_download_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] in ("client_reported_complete", "failed"):
        return {"status": session["status"], "idempotent": True}
    sanitized = payload.reason[:100]
    await session_repo.update_download_session(db, session_id, "failed", failure_reason=sanitized)
    await event_repo.record_event(
        db, new_id("evt"), session["file_id"], "download_failed", "failed",
        share_link_id=session["share_link_id"], download_session_id=session_id,
        metadata={"reason": sanitized},
    )
    return {"status": "failed"}