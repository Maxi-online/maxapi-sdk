from __future__ import annotations

from typing import Any

from ..filters.base import BaseFilter
from .middleware import build_storage_key
from .state import State


class StateFilter(BaseFilter):
    def __init__(self, *states: State | str) -> None:
        self.states = {_normalize_state(item) for item in states}

    async def __call__(self, event: Any) -> bool:
        bot = getattr(event, "bot", None)
        dispatcher = getattr(bot, "dispatcher", None)
        storage = getattr(dispatcher, "fsm_storage", None)
        if storage is None:
            return False
        key = build_storage_key(event)
        if key is None:
            return False
        current_state = await storage.get_state(key)
        return current_state in self.states


def _normalize_state(state: State | str) -> str:
    if isinstance(state, State):
        return str(state)
    return state
