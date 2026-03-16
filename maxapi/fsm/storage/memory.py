from __future__ import annotations

from typing import Any

from .base import StorageKey


class MemoryStorage:
    """In-memory storage для FSM."""

    def __init__(self) -> None:
        self._states: dict[StorageKey, str | None] = {}
        self._data: dict[StorageKey, dict[str, Any]] = {}

    async def get_state(self, key: StorageKey) -> str | None:
        return self._states.get(key)

    async def set_state(self, key: StorageKey, state: str | None) -> None:
        if state is None:
            self._states.pop(key, None)
            return
        self._states[key] = state

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        return dict(self._data.get(key, {}))

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        self._data[key] = dict(data)

    async def update_data(self, key: StorageKey, data: dict[str, Any]) -> dict[str, Any]:
        current = await self.get_data(key)
        current.update(data)
        await self.set_data(key, current)
        return current

    async def clear(self, key: StorageKey) -> None:
        self._states.pop(key, None)
        self._data.pop(key, None)
