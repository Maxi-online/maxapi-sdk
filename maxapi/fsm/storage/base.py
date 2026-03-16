from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class StorageKey:
    chat_id: int | None
    user_id: int | None


class BaseStorage(Protocol):
    async def get_state(self, key: StorageKey) -> str | None:
        ...

    async def set_state(self, key: StorageKey, state: str | None) -> None:
        ...

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        ...

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        ...

    async def update_data(self, key: StorageKey, data: dict[str, Any]) -> dict[str, Any]:
        ...

    async def clear(self, key: StorageKey) -> None:
        ...
