from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientTimeout


@dataclass(slots=True)
class RetryPolicy:
    """Политика повторов HTTP-запросов."""

    attempts: int = 5
    initial_delay: float = 0.5
    backoff: float = 2.0
    max_delay: float = 8.0
    respect_retry_after: bool = True
    retry_statuses: tuple[int, ...] = (408, 425, 429, 500, 502, 503, 504)
    retry_methods: tuple[str, ...] = (
        "DELETE",
        "GET",
        "HEAD",
        "OPTIONS",
        "PATCH",
        "POST",
        "PUT",
    )

    def delay_for_attempt(
        self,
        attempt_index: int,
        *,
        retry_after: float | None = None,
    ) -> float:
        if self.respect_retry_after and retry_after is not None and retry_after > 0:
            return min(retry_after, self.max_delay)
        delay = self.initial_delay * (self.backoff ** max(attempt_index - 1, 0))
        return min(delay, self.max_delay)

    def allows(self, method: str, status: int | None = None) -> bool:
        normalized_method = method.upper()
        if normalized_method not in self.retry_methods:
            return False
        if status is None:
            return True
        return status in self.retry_statuses


@dataclass(slots=True)
class TransportConfig:
    """Конфигурация транспортного клиента."""

    timeout: ClientTimeout
    session_kwargs: dict[str, Any]
    retry_policy: RetryPolicy

    @classmethod
    def from_default_connection(cls, connection: Any) -> "TransportConfig":
        retry_policy = RetryPolicy(
            attempts=getattr(connection, "request_retries", 5),
            initial_delay=getattr(connection, "request_retry_delay", 0.5),
            backoff=getattr(connection, "request_retry_backoff", 2.0),
            max_delay=getattr(connection, "request_retry_max_delay", 8.0),
            respect_retry_after=getattr(connection, "respect_retry_after", True),
            retry_statuses=tuple(
                getattr(connection, "retry_statuses", (408, 425, 429, 500, 502, 503, 504))
            ),
            retry_methods=tuple(
                getattr(
                    connection,
                    "retry_methods",
                    ("DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"),
                )
            ),
        )
        session_kwargs = dict(getattr(connection, "kwargs", {}))
        return cls(
            timeout=connection.timeout,
            session_kwargs=session_kwargs,
            retry_policy=retry_policy,
        )
