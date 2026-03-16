from __future__ import annotations

import asyncio
from typing import Iterable

from ..types import UpdateType


class PollingRunner:
    """Отдельный runtime-класс для long polling."""

    def __init__(
        self,
        *,
        bot,
        dispatcher,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: Iterable[UpdateType | str] | None = None,
        retry_delay: float = 2.0,
        raise_exceptions: bool = False,
    ) -> None:
        self.bot = bot
        self.dispatcher = dispatcher
        self.limit = limit
        self.timeout = timeout
        self.allowed_updates = list(allowed_updates or [])
        self.retry_delay = retry_delay
        self.raise_exceptions = raise_exceptions
        self._stop_event = asyncio.Event()

    async def run_once(self) -> None:
        page = await self.bot.get_updates(
            marker=self.bot.marker_updates,
            limit=self.limit,
            timeout=self.timeout,
            types=self.allowed_updates or None,
        )
        for update in page.updates:
            await self.dispatcher.process_update(update, bot=self.bot)
        self.bot.marker_updates = page.marker

    async def start(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                if self.raise_exceptions:
                    raise
                await asyncio.sleep(self.retry_delay)

    async def stop(self) -> None:
        self._stop_event.set()
