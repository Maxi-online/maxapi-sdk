from __future__ import annotations

import re
from typing import Any, Pattern

from .base import BaseFilter


class Text(BaseFilter):
    """Точное совпадение текста сообщения."""

    def __init__(self, value: str, *, case_sensitive: bool = False, strip: bool = True) -> None:
        self.value = value
        self.case_sensitive = case_sensitive
        self.strip = strip

    async def __call__(self, event: Any) -> bool:
        text = _get_message_text(event)
        if text is None:
            return False
        if self.strip:
            text = text.strip()
        if self.case_sensitive:
            return text == self.value
        return text.lower() == self.value.lower()


class TextContains(BaseFilter):
    def __init__(self, value: str, *, case_sensitive: bool = False) -> None:
        self.value = value
        self.case_sensitive = case_sensitive

    async def __call__(self, event: Any) -> bool:
        text = _get_message_text(event)
        if text is None:
            return False
        if self.case_sensitive:
            return self.value in text
        return self.value.lower() in text.lower()


class TextStartsWith(BaseFilter):
    def __init__(self, value: str, *, case_sensitive: bool = False) -> None:
        self.value = value
        self.case_sensitive = case_sensitive

    async def __call__(self, event: Any) -> bool:
        text = _get_message_text(event)
        if text is None:
            return False
        if self.case_sensitive:
            return text.startswith(self.value)
        return text.lower().startswith(self.value.lower())


class Regex(BaseFilter):
    def __init__(self, pattern: str | Pattern[str], *, flags: int = 0) -> None:
        self.pattern = re.compile(pattern, flags) if isinstance(pattern, str) else pattern

    async def __call__(self, event: Any) -> bool:
        text = _get_message_text(event)
        if text is None:
            return False
        return self.pattern.search(text) is not None


def _get_message_text(event: Any) -> str | None:
    message = getattr(event, "message", None)
    if message is None or getattr(message, "body", None) is None:
        return None
    return getattr(message.body, "text", None)
