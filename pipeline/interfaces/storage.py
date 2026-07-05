from abc import ABC, abstractmethod
from typing import Any


class StorageProvider(ABC):
    @abstractmethod
    async def save_asset(
        self, source_url: str, destination: str, *,
        metadata: dict | None = None,
    ) -> str: ...

    @abstractmethod
    async def get_asset_url(self, path: str) -> str: ...

    @abstractmethod
    async def delete_asset(self, path: str) -> bool: ...

    @abstractmethod
    async def list_assets(self, prefix: str) -> list[dict[str, Any]]: ...
