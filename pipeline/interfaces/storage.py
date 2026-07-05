from abc import ABC, abstractmethod
from typing import Any
import os
import shutil
import requests
from loguru import logger


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


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_path: str = "./assets"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    async def save_asset(
        self, source_url: str, destination: str, *,
        metadata: dict | None = None,
    ) -> str:
        dest_path = os.path.join(self.base_path, destination)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        if source_url.startswith("http"):
            try:
                resp = requests.get(source_url, stream=True, timeout=30)
                resp.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Downloaded: {source_url} → {dest_path}")
            except Exception as e:
                logger.error(f"Download failed {source_url}: {e}")
                raise
        else:
            shutil.copy2(source_url, dest_path)

        return dest_path

    async def get_asset_url(self, path: str) -> str:
        full = os.path.join(self.base_path, path) if not path.startswith("/") else path
        return f"file://{os.path.abspath(full)}"

    async def delete_asset(self, path: str) -> bool:
        full = os.path.join(self.base_path, path) if not path.startswith("/") else path
        if os.path.exists(full):
            os.remove(full)
            return True
        return False

    async def list_assets(self, prefix: str) -> list[dict[str, Any]]:
        search_path = os.path.join(self.base_path, prefix)
        if not os.path.exists(search_path):
            return []
        results = []
        for root, dirs, files in os.walk(search_path):
            for f in files:
                full = os.path.join(root, f)
                results.append({
                    "path": os.path.relpath(full, self.base_path),
                    "size": os.path.getsize(full),
                    "name": f,
                })
        return results
