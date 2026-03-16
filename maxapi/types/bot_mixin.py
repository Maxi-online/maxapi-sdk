from __future__ import annotations

from typing import Any


class BotMixin:
    """Предоставляет безопасный доступ к экземпляру бота."""

    bot: Any | None = None

    def _ensure_bot(self) -> Any:
        if self.bot is None:
            raise RuntimeError("Экземпляр Bot не привязан к текущему объекту.")
        return self.bot
