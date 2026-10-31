from abc import ABC, abstractmethod


class StorageBase(ABC):
    @abstractmethod
    def presign_upload(self, key: str, session_id: str, expires: int) -> str:
        ...

    @abstractmethod
    def presign_download(self, key: str, file_id: str, expires: int) -> str:
        ...

    @abstractmethod
    async def head_object(self, key: str) -> dict | None:
        ...

    @abstractmethod
    async def delete_object(self, key: str) -> bool:
        ...

    @abstractmethod
    def is_local(self) -> bool:
        ...