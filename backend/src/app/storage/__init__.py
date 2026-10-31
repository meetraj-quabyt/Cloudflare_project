from app.core.config import settings
from app.storage.base import StorageBase
from app.storage.r2 import R2Client


def get_storage() -> StorageBase:
    if settings.r2_account_id and settings.r2_access_key_id and settings.r2_secret_access_key and settings.r2_bucket_name:
        return R2Client()
    from app.storage.local import LocalStorage
    return LocalStorage()