from __future__ import annotations

from typing import Any

from .storage.base import BaseStorage, StorageKey
from .state import State


class FSMContext:
    """Контекст состояния для конкретного chat_id/user_id."""

    def __init__(self, *, storage: BaseStorage, key: StorageKey) -> None:
        self.storage = storage
        self.key = key

    async def get_state(self) -> str | None:
        return await self.storage.get_state(self.key)

    async def set_state(self, state: State | str | None) -> None:
        normalized = _normalize_state(state)
        await self.storage.set_state(self.key, normalized)

    async def get_data(self) -> dict[str, Any]:
        return await self.storage.get_data(self.key)

    async def set_data(self, data: dict[str, Any]) -> None:
        await self.storage.set_data(self.key, data)

    async def update_data(self, **kwargs: Any) -> dict[str, Any]:
        return await self.storage.update_data(self.key, kwargs)

    async def clear(self) -> None:
        await self.storage.clear(self.key)


def _normalize_state(state: State | str | None) -> str | None:
    if state is None:
        return None
    if isinstance(state, State):
        return str(state)
    return state
