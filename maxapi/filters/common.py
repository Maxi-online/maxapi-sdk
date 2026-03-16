from __future__ import annotations

from typing import Any

from ..callback_schema import extract_callback_value
from .base import BaseFilter


class ChatId(BaseFilter):
    def __init__(self, *chat_ids: int) -> None:
        self.chat_ids = set(chat_ids)

    async def __call__(self, event: Any) -> bool:
        chat_id = getattr(event, "chat_id", None)
        return chat_id in self.chat_ids


class UserId(BaseFilter):
    def __init__(self, *user_ids: int) -> None:
        self.user_ids = set(user_ids)

    async def __call__(self, event: Any) -> bool:
        user_id = getattr(event, "user_id", None)
        return user_id in self.user_ids


class CallbackData(BaseFilter):
    def __init__(
        self,
        value: str,
        *,
        case_sensitive: bool = True,
        startswith: bool = False,
        contains: bool = False,
    ) -> None:
        self.value = value
        self.case_sensitive = case_sensitive
        self.startswith = startswith
        self.contains = contains

    async def __call__(self, event: Any) -> bool:
        callback = getattr(getattr(event, "update", None), "callback", None)
        payload = getattr(callback, "payload", None)
        payload_value = extract_callback_value(payload)
        if payload_value is None:
            return False
        return self._compare(payload_value)

    def _compare(self, other: str) -> bool:
        left = other if self.case_sensitive else other.lower()
        right = self.value if self.case_sensitive else self.value.lower()
        if self.startswith:
            return left.startswith(right)
        if self.contains:
            return right in left
        return left == right


class HasAttachments(BaseFilter):
    async def __call__(self, event: Any) -> bool:
        message = getattr(event, "message", None)
        if message is None or getattr(message, "body", None) is None:
            return False
        attachments = getattr(message.body, "attachments", None)
        return bool(attachments)


class ChatType(BaseFilter):
    def __init__(self, *chat_types: str) -> None:
        self.chat_types = {value.lower() for value in chat_types}

    async def __call__(self, event: Any) -> bool:
        message = getattr(event, "message", None)
        recipient = getattr(message, "recipient", None) if message is not None else None
        recipient_type = getattr(recipient, "type", None)
        if recipient_type is None:
            return False
        return recipient_type.lower() in self.chat_types
