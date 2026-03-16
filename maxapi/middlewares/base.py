from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable

MiddlewareHandler = Callable[[Any, dict[str, Any]], Awaitable[Any]]


class BaseMiddleware:
    """Базовый middleware."""

    async def __call__(
        self,
        handler: MiddlewareHandler,
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        return await handler(event, data)


class FunctionMiddleware(BaseMiddleware):
    def __init__(self, callback: Callable[[MiddlewareHandler, Any, dict[str, Any]], Any]) -> None:
        self.callback = callback

    async def __call__(
        self,
        handler: MiddlewareHandler,
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        result = self.callback(handler, event, data)
        if inspect.isawaitable(result):
            return await result
        return result
