from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable, Protocol


class FilterLike(Protocol):
    async def __call__(self, event: Any) -> bool:  # pragma: no cover - typing protocol
        ...


class BaseFilter:
    """Базовый фильтр с поддержкой композиции."""

    async def __call__(self, event: Any) -> bool:
        raise NotImplementedError

    def __and__(self, other: Any) -> "AndFilter":
        return AndFilter(self, ensure_filter(other))

    def __or__(self, other: Any) -> "OrFilter":
        return OrFilter(self, ensure_filter(other))

    def __invert__(self) -> "NotFilter":
        return NotFilter(self)


class CallableFilter(BaseFilter):
    def __init__(self, callback: Callable[[Any], Awaitable[bool] | bool]) -> None:
        self.callback = callback

    async def __call__(self, event: Any) -> bool:
        result = self.callback(event)
        if inspect.isawaitable(result):
            result = await result
        return bool(result)


class MultiFilter(BaseFilter):
    def __init__(self, *filters: BaseFilter) -> None:
        self.filters = list(filters)


class AndFilter(MultiFilter):
    async def __call__(self, event: Any) -> bool:
        for item in self.filters:
            if not await item(event):
                return False
        return True


class OrFilter(MultiFilter):
    async def __call__(self, event: Any) -> bool:
        for item in self.filters:
            if await item(event):
                return True
        return False


class NotFilter(BaseFilter):
    def __init__(self, inner: BaseFilter) -> None:
        self.inner = inner

    async def __call__(self, event: Any) -> bool:
        return not await self.inner(event)


def ensure_filter(candidate: Any) -> BaseFilter:
    if isinstance(candidate, BaseFilter):
        return candidate
    if callable(candidate):
        return CallableFilter(candidate)
    raise TypeError(f"Неподдерживаемый фильтр: {candidate!r}")
