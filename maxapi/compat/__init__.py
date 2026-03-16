from __future__ import annotations

from ..bot import Bot as LegacyBot
from ..builders import InlineKeyboardBuilder as Keyboard
from ..dispatcher import Dispatcher as LegacyDispatcher
from ..dispatcher import Router as LegacyRouter
from ..types import MessageBody as NewMessageBody

__all__ = [
    "Keyboard",
    "LegacyBot",
    "LegacyDispatcher",
    "LegacyRouter",
    "NewMessageBody",
]
