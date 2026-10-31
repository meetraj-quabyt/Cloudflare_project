from fastapi import APIRouter, Query, Request

from app.core.config import settings
from app.repositories import event_repo

router = APIRouter(prefix="/activity", tags=["activity"])


def get_db(request):
    return request.app.state.db


def get_owner(request, owner_token=None):
    owner = request.headers.get(settings.anonymous_owner_header)
    if not owner and owner_token:
        owner = owner_token
    if not owner:
        owner = request.client.host if request.client else "anonymous"
    return owner


@router.get("")
async def activity(request: Request, file_id: str | None = None, event_type: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), since: str | None = None, until: str | None = None, owner_token: str | None = None):
    db = get_db(request)
    owner = get_owner(request, owner_token)
    rows = await event_repo.list_events(db, owner_token=owner, file_id=file_id, event_type=event_type, limit=limit, offset=offset, since=since, until=until)
    total = await event_repo.count_events(db, owner_token=owner, file_id=file_id, event_type=event_type)
    return {"items": rows, "total": total, "limit": limit, "offset": offset}