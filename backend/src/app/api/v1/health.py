from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request):
    db = request.app.state.db
    storage = request.app.state.storage
    db_ok = True
    try:
        await db.fetch_one("SELECT 1 as x")
    except Exception:  # noqa: BLE001
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "storage": "configured" if (storage is not None and not storage.is_local()) else "local",
    }