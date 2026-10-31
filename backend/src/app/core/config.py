from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CloudShare"
    environment: str = "development"
    backend_base_url: str = "http://localhost:8000"
    frontend_origin: str = "http://localhost:5173"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    # R2 / S3-compatible storage
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "cloudshare-files"
    r2_region: str = "auto"
    r2_endpoint_url: str = ""

    # D1 / SQLite
    database_url: str = "sqlite+aiosqlite:///./cloudshare.db"  # local dev fallback
    d1_database_id: str = ""

    # Limits
    max_file_size_bytes: int = 100 * 1024 * 1024  # 100 MB
    default_share_expires_hours: int = 24 * 7
    default_max_downloads: int | None = None
    upload_url_ttl_seconds: int = 900  # 15 min
    download_url_ttl_seconds: int = 300  # 5 min
    upload_session_ttl_minutes: int = 60
    download_session_ttl_minutes: int = 60

    # Security
    rate_limit_per_minute: int = 60
    anonymous_owner_header: str = "X-CloudShare-Owner"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def r2_endpoint(self) -> str:
        if self.r2_endpoint_url:
            return self.r2_endpoint_url
        if self.r2_account_id:
            return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"
        return ""

    def is_r2_configured(self) -> bool:
        return bool(self.r2_access_key_id and self.r2_secret_access_key and self.r2_bucket_name and self.r2_endpoint)


settings = Settings()