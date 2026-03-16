from __future__ import annotations

from typing import Protocol


class PluginProtocol(Protocol):
    name: str

    def setup(self, router) -> None:
        ...


class BasePlugin:
    """Базовый плагин для расширения Router/Dispatcher."""

    name = "base"

    def setup(self, router) -> None:  # pragma: no cover - interface hook
        raise NotImplementedError
