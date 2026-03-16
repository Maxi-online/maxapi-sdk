from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import BaseFilter


@dataclass(slots=True)
class Command(BaseFilter):
    """Фильтр команды по тексту сообщения."""

    name: str
    prefix: str = "/"
    case_sensitive: bool = False

    async def __call__(self, event: Any) -> bool:
        message = getattr(event, "message", None)
        if message is None or message.body is None or message.body.text is None:
            return False
        text = message.body.text.strip()
        if not text:
            return False
        first_token = text.split(maxsplit=1)[0]
        command_value = f"{self.prefix}{self.name}"
        if self.case_sensitive:
            return first_token == command_value
        return first_token.lower() == command_value.lower()
