import hashlib
import hmac
from datetime import UTC, datetime
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.storage.base import StorageBase


def _signing_key(secret: str, datestamp: str, region: str, service: str = "s3") -> bytes:
    k_date = hmac.new(("AWS4" + secret).encode(), datestamp.encode(), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region.encode(), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode(), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()
    return k_signing


def _amz_date() -> tuple[str, str]:
    now = datetime.now(UTC)
    return now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y%m%d")


class R2Client(StorageBase):
    def __init__(self):
        self.account_id = settings.r2_account_id
        self.access_key = settings.r2_access_key_id
        self.secret = settings.r2_secret_access_key
        self.bucket = settings.r2_bucket_name
        self.region = settings.r2_region or "auto"
        self.endpoint = settings.r2_endpoint.rstrip("/")

    def _configured(self) -> bool:
        return bool(self.access_key and self.secret and self.bucket and self.endpoint)

    def presign_url(self, method: str, key: str, expires: int) -> str:
        if not self._configured():
            # return a placeholder (tests mock storage)
            return f"{self.endpoint}/{self.bucket}/{key}?unsigned=1"
        amz_date, datestamp = _amz_date()
        credential_scope = f"{datestamp}/{self.region}/s3/aws4_request"
        credential = f"{self.access_key}/{credential_scope}"
        host = self.endpoint.replace("https://", "").replace("http://", "")
        # path
        encoded_key = quote(key, safe="/")
        canonical_uri = f"/{self.bucket}/{encoded_key}"

        params = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": credential,
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(expires),
            "X-Amz-SignedHeaders": "host",
        }
        # sorted query string
        sorted_params = sorted(params.items())
        canonical_querystring = "&".join(f"{quote(k, safe='')}={quote(str(v), safe='')}" for k, v in sorted_params)

        canonical_headers = f"host:{host}\n"
        signed_headers = "host"
        payload_hash = "UNSIGNED-PAYLOAD"

        canonical_request = "\n".join([  # noqa: FLY002
            method.upper(),
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            payload_hash,
        ])

        string_to_sign = "\n".join([
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ])

        signing_key = _signing_key(self.secret, datestamp, self.region)
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

        url = f"{self.endpoint}{canonical_uri}?{canonical_querystring}&X-Amz-Signature={signature}"
        return url

    def is_local(self) -> bool:
        return False

    def presign_upload(self, key: str, session_id: str = "", expires: int = 0) -> str:
        return self.presign_url("PUT", key, expires)

    def presign_download(self, key: str, file_id: str = "", expires: int = 0) -> str:
        return self.presign_url("GET", key, expires)

    async def head_object(self, key: str) -> dict | None:
        if not self._configured():
            return None
        # signed HEAD request
        url = f"{self.endpoint}/{self.bucket}/{quote(key, safe='/')}"
        headers = await self._signed_headers("HEAD", f"/{self.bucket}/{quote(key, safe='/')}", "")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.head(url, headers=headers)
            if r.status_code == 404:
                return None
            if r.status_code >= 400:
                return None
            size = r.headers.get("content-length")
            ct = r.headers.get("content-type")
            etag = r.headers.get("etag")
            return {
                "size": int(size) if size else None,
                "content_type": ct,
                "etag": etag,
            }
        except Exception:  # noqa: BLE001
            return None

    async def delete_object(self, key: str) -> bool:
        if not self._configured():
            return True
        path = f"/{self.bucket}/{quote(key, safe='/')}"
        url = f"{self.endpoint}{path}"
        headers = await self._signed_headers("DELETE", path, "")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.delete(url, headers=headers)
            return r.status_code in (200, 204, 404)
        except Exception:  # noqa: BLE001
            return False

    async def _signed_headers(self, method: str, canonical_uri: str, query: str) -> dict:
        amz_date, datestamp = _amz_date()
        host = self.endpoint.replace("https://", "").replace("http://", "")
        payload_hash = hashlib.sha256(b"").hexdigest()
        canonical_headers = f"host:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
        signed_headers = "host;x-amz-content-sha256;x-amz-date"
        canonical_request = "\n".join([  # noqa: FLY002
            method.upper(),
            canonical_uri,
            query,
            canonical_headers,
            signed_headers,
            payload_hash,
        ])
        credential_scope = f"{datestamp}/{self.region}/s3/aws4_request"
        string_to_sign = "\n".join([
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ])
        signing_key = _signing_key(self.secret, datestamp, self.region)
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
        authorization = (
            f"AWS4-HMAC-SHA256 Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        return {
            "Host": host,
            "x-amz-date": amz_date,
            "x-amz-content-sha256": payload_hash,
            "Authorization": authorization,
        }