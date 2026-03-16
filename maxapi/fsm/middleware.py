from __future__ import annotations

from typing import Any

from ..middlewares import BaseMiddleware, MiddlewareHandler
from .context import FSMContext
from .storage.base import BaseStorage, StorageKey


class FSMMiddleware(BaseMiddleware):
    """Middleware, который внедряет FSMContext в handlers."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage

    async def __call__(
        self,
        handler: MiddlewareHandler,
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        key = build_storage_key(event)
        if key is None:
            data.setdefault("state", None)
            data.setdefault("fsm_context", None)
            data.setdefault("raw_state", None)
            data.setdefault("state_data", {})
            return await handler(event, data)
        context = FSMContext(storage=self.storage, key=key)
        data["fsm_context"] = context
        data["state"] = context
        data["raw_state"] = await context.get_state()
        data["state_data"] = await context.get_data()
        return await handler(event, data)


def build_storage_key(event: Any) -> StorageKey | None:
    chat_id = getattr(event, "chat_id", None)
    user_id = getattr(event, "user_id", None)
    if chat_id is None and user_id is None:
        return None
    return StorageKey(chat_id=chat_id, user_id=user_id)
