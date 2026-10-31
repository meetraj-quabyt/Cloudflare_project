import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import activity, chat, downloads, files, health, shares, uploads
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.repositories.db import Database
from app.storage import get_storage

log = get_logger("main")


def build_database(env=None) -> Database:
    import os

    # Container mode: use D1 REST API when running inside a Cloudflare Container
    if os.getenv("CF_CONTAINER") == "1" or (
        os.getenv("CLOUDFLARE_D1_TOKEN") and os.getenv("CF_D1_DATABASE_ID")
    ):
        from app.repositories.db_d1_rest import D1RestDatabase

        return D1RestDatabase()  # type: ignore[return-value]

    # Worker mode: use D1 binding
    if env is not None and getattr(env, "DB", None) is not None:
        return Database(d1_binding=env.DB)

    # Local dev: sqlite fallback
    url = settings.database_url
    path = url
    if url.startswith("sqlite"):
        # sqlite+aiosqlite:///./x.db or sqlite:///./x.db
        path = url.split("///")[-1]
    return Database(sqlite_path=path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db: Database = app.state.db
    await db.connect()
    # apply migrations if sqlite
    if not db.is_d1:
        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "migrations", "0001_init.sql")) as f:  # noqa: ASYNC230
                await db.executescript(f.read())
        except FileNotFoundError:
            pass
    if getattr(app.state, "storage", None) is None:
        try:
            app.state.storage = get_storage()
        except Exception as e:  # noqa: BLE001
            log.warning("storage_init_failed", error=str(e))
    yield
    await db.close()


def create_app(env=None) -> FastAPI:
    setup_logging()
    if env is not None:
        mapping = {
            "R2_ACCOUNT_ID": "r2_account_id",
            "R2_ACCESS_KEY_ID": "r2_access_key_id",
            "R2_SECRET_ACCESS_KEY": "r2_secret_access_key",
            "R2_BUCKET_NAME": "r2_bucket_name",
            "R2_REGION": "r2_region",
            "R2_ENDPOINT_URL": "r2_endpoint_url",
            "DATABASE_URL": "database_url",
            "FRONTEND_BASE_URL": "backend_base_url",
            "MAX_FILE_SIZE_BYTES": "max_file_size_bytes",
            "ALLOWED_ORIGINS": "allowed_origins",
            "FRONTEND_ORIGIN": "frontend_origin",
            "AZURE_OPENAI_API_KEY": "azure_openai_api_key",
            "AZURE_OPENAI_ENDPOINT": "azure_openai_endpoint",
            "DEPLOYMENT_NAME": "deployment_name",
            "AZURE_OPENAI_API_VERSION": "azure_openai_api_version",
        }
        for env_key, field in mapping.items():
            val = getattr(env, env_key, None)
            if val is not None:
                os.environ[env_key] = str(val)
                try:
                    setattr(settings, field, type(getattr(settings, field))(val) if not isinstance(val, str) else val)
                except Exception:  # noqa: BLE001
                    setattr(settings, field, val)
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.env = env
    app.state.db = build_database(env)
    app.state.settings = settings

    origins = settings.origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # request id middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        start = time.time()
        response = await call_next(request)
        response.headers["x-request-id"] = rid
        dur = int((time.time() - start) * 1000)
        log.info("request", method=request.method, path=request.url.path, status=response.status_code, duration_ms=dur, request_id=rid)
        return response

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(uploads.router, prefix="/api/v1")
    app.include_router(files.router, prefix="/api/v1")
    app.include_router(shares.router, prefix="/api/v1")
    app.include_router(downloads.router, prefix="/api/v1")
    app.include_router(activity.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")

    @app.exception_handler(Exception)
    async def generic_exc(request: Request, exc: Exception):
        log.error("unhandled", error=str(exc), path=request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


# module-level app for uvicorn
app = create_app()