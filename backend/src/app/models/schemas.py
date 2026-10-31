
from pydantic import BaseModel, Field


class InitiateUploadRequest(BaseModel):
    filename: str
    content_type: str
    size_bytes: int = Field(gt=0)
    checksum_sha256: str | None = None
    owner_token: str | None = None


class InitiateUploadResponse(BaseModel):
    session_id: str
    file_id: str
    upload_url: str
    upload_method: str = "PUT"
    required_headers: dict = {}
    expires_at: str


class CompleteUploadRequest(BaseModel):
    checksum_sha256: str | None = None


class UploadStatusResponse(BaseModel):
    session_id: str
    file_id: str
    status: str
    expected_size_bytes: int
    actual_size_bytes: int | None = None
    failure_reason: str | None = None


class ShareCreateRequest(BaseModel):
    expires_in_hours: int | None = None
    max_downloads: int | None = None
    owner_token: str | None = None


class ShareCreateResponse(BaseModel):
    share_id: str
    share_url: str
    expires_at: str | None = None
    max_downloads: int | None = None


class PublicShareInfo(BaseModel):
    file_name: str
    size_bytes: int
    content_type: str
    upload_date: str | None = None
    expires_at: str | None = None
    remaining_downloads: int | None = None
    is_active: bool


class DownloadInitiateResponse(BaseModel):
    download_session_id: str
    download_url: str
    expires_at: str
    file_name: str
    size_bytes: int


class CompleteDownloadRequest(BaseModel):
    bytes_transferred: int | None = None
    client_reported: bool = True


class FailDownloadRequest(BaseModel):
    reason: str


class FileOut(BaseModel):
    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    upload_status: str
    created_at: str
    uploaded_at: str | None = None
    expires_at: str | None = None


class ActivityEvent(BaseModel):
    id: str
    file_id: str
    event_type: str
    status: str
    occurred_at: str
    bytes_transferred: int | None = None
    metadata_json: str | None = None