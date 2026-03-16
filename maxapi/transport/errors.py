from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TransportResponseError(Exception):
    """Базовая ошибка transport-слоя."""

    status: int
    payload: Any
    message: str | None = None
    headers: dict[str, str] | None = None

    def __str__(self) -> str:
        if self.message:
            return self.message
        return f"Transport error status={self.status}: {self.payload!r}"


@dataclass(slots=True)
class RateLimitExceededError(TransportResponseError):
    """Ошибка 429 Too Many Requests."""

    retry_after: float | None = None


@dataclass(slots=True)
class ServerResponseError(TransportResponseError):
    """Ошибка 5xx от API MAX."""


@dataclass(slots=True)
class ResponseDecodeError(Exception):
    """Ошибка декодирования ответа сервера."""

    text: str
    content_type: str | None = None

    def __str__(self) -> str:
        return (
            "Не удалось декодировать ответ сервера MAX как JSON. "
            f"content_type={self.content_type!r}"
        )
