from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aiohttp import ClientTimeout


@dataclass(slots=True)
class DefaultConnectionProperties:
    """Расширенная конфигурация HTTP-соединения."""

    timeout_seconds: float = 150.0
    sock_connect: float = 30.0
    sock_read: float = 60.0
    connector_limit: int = 100
    connector_limit_per_host: int = 30
    trust_env: bool = False
    auto_decompress: bool = True
    raise_for_status: bool = False
    request_retries: int = 5
    request_retry_delay: float = 0.5
    request_retry_backoff: float = 2.0
    request_retry_max_delay: float = 8.0
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
    timeout: ClientTimeout = field(init=False)
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        timeout: float = 150.0,
        sock_connect: float = 30.0,
        sock_read: float = 60.0,
        connector_limit: int = 100,
        connector_limit_per_host: int = 30,
        trust_env: bool = False,
        auto_decompress: bool = True,
        raise_for_status: bool = False,
        request_retries: int = 5,
        request_retry_delay: float = 0.5,
        request_retry_backoff: float = 2.0,
        request_retry_max_delay: float = 8.0,
        respect_retry_after: bool = True,
        retry_statuses: tuple[int, ...] | None = None,
        retry_methods: tuple[str, ...] | None = None,
        **kwargs: Any,
    ) -> None:
        self.timeout_seconds = timeout
        self.sock_connect = sock_connect
        self.sock_read = sock_read
        self.connector_limit = connector_limit
        self.connector_limit_per_host = connector_limit_per_host
        self.trust_env = trust_env
        self.auto_decompress = auto_decompress
        self.raise_for_status = raise_for_status
        self.request_retries = request_retries
        self.request_retry_delay = request_retry_delay
        self.request_retry_backoff = request_retry_backoff
        self.request_retry_max_delay = request_retry_max_delay
        self.respect_retry_after = respect_retry_after
        self.retry_statuses = retry_statuses or (408, 425, 429, 500, 502, 503, 504)
        self.retry_methods = retry_methods or (
            "DELETE",
            "GET",
            "HEAD",
            "OPTIONS",
            "PATCH",
            "POST",
            "PUT",
        )
        self.timeout = ClientTimeout(
            total=timeout,
            sock_connect=sock_connect,
            sock_read=sock_read,
        )
        self.kwargs = dict(kwargs)
        self.kwargs.setdefault("trust_env", trust_env)
        self.kwargs.setdefault("auto_decompress", auto_decompress)
        self.kwargs.setdefault("raise_for_status", raise_for_status)
