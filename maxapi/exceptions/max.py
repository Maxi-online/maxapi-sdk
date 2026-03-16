from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class MaxError(Exception):
    """Базовая ошибка SDK."""


class MaxConnection(MaxError):
    """Ошибка сетевого уровня."""


@dataclass(slots=True)
class MaxApiError(MaxError):
    """Ошибка ответа MAX API."""

    code: int
    raw: Any
    message: str | None = None
    headers: dict[str, str] | None = None

    def __str__(self) -> str:
        if self.message:
            return self.message
        return f"MAX API returned status={self.code}: {self.raw!r}"


class InvalidToken(MaxApiError):
    """Ошибка авторизации API MAX."""

    def __init__(
        self,
        message: str = "Неверный токен!",
        *,
        raw: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            code=401,
            raw=raw if raw is not None else {"message": message},
            message=message,
            headers=headers,
        )
