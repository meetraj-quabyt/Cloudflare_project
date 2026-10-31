import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta


def new_id(prefix: str = "") -> str:
    return (prefix + "_" if prefix else "") + uuid.uuid4().hex


def new_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def safe_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def utc_future(minutes: int | None = None, hours: int | None = None, seconds: int | None = None) -> str:
    delta = timedelta()
    if minutes:
        delta += timedelta(minutes=minutes)
    if hours:
        delta += timedelta(hours=hours)
    if seconds:
        delta += timedelta(seconds=seconds)
    return (datetime.now(UTC) + delta).isoformat()


def parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))  # noqa: FURB162
    except ValueError:
        return None


def is_expired(s: str | None) -> bool:
    dt = parse_iso(s)
    if dt is None:
        return False
    return dt < datetime.now(UTC)


def sanitize_filename(name: str) -> str:
    # strip path components and dangerous chars
    base = name.replace("\\", "/").split("/")[-1]
    base = base.strip()
    # remove control chars
    base = "".join(c for c in base if c.isprintable() and c not in "\x00<>:\"|?*")
    if not base or base in (".", ".."):
        return "file"
    if len(base) > 255:
        base = base[:255]
    return base


ALLOWED_CONTENT_TYPES = {
    "image/png", "image/jpeg", "image/gif", "image/webp", "image/svg+xml",
    "application/pdf", "text/plain", "text/csv", "text/markdown",
    "application/json", "application/zip", "application/gzip",
    "application/octet-stream", "video/mp4", "audio/mpeg",
}


def is_allowed_content_type(ct: str) -> bool:
    ct = ct.split(";")[0].strip().lower()
    if ct in ALLOWED_CONTENT_TYPES:
        return True
    # allow any text/* and image/* and application/* generically but block scripts
    if ct.startswith(("text/", "image/", "video/", "audio/")):
        return True
    return ct.startswith("application/")