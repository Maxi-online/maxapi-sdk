from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles
from aiohttp import FormData

from ..transport import MaxApiTransport, TransportConfig
from ..types.bot_mixin import BotMixin

if TYPE_CHECKING:
    from aiohttp import ClientSession


class BaseConnection(BotMixin):
    """Базовый класс transport-aware соединения."""

    API_URL = "https://platform-api.max.ru"

    def __init__(self) -> None:
        self.bot = None
        self.session: ClientSession | None = None
        self.api_url = self.API_URL
        self._transport: MaxApiTransport | None = None

    def set_api_url(self, url: str) -> None:
        self.api_url = url.rstrip("/")
        if self.bot is not None:
            self.bot.api_url = self.api_url
        self._transport = None

    async def request(
        self,
        method: str,
        path: str,
        model: Any = None,
        *,
        is_return_raw: bool = False,
        **kwargs: Any,
    ) -> Any:
        bot = self._ensure_bot()
        transport = self._ensure_transport(bot)
        response = await transport.request(method=method, path=path, model=model, **kwargs)
        if is_return_raw:
            return response.raw
        parsed = response.parsed
        self._bind_bot(bot=bot, payload=parsed)
        return parsed

    async def upload_file(self, url: str, path: str, upload_type: str) -> Any:
        async with aiofiles.open(path, "rb") as file_object:
            file_data = await file_object.read()
        filename = Path(path).name
        return await self.upload_file_buffer(
            filename=filename,
            url=url,
            buffer=file_data,
            upload_type=upload_type,
        )

    async def upload_file_buffer(
        self,
        *,
        filename: str,
        url: str,
        buffer: bytes,
        upload_type: str,
    ) -> Any:
        ext = Path(filename).suffix
        if not ext:
            guessed_ext = mimetypes.guess_extension(f"{upload_type}/*") or ""
            ext = guessed_ext
        content_type = mimetypes.guess_type(filename)[0] or f"{upload_type}/*"
        form = FormData(quote_fields=False)
        form.add_field(
            name="data",
            value=buffer,
            filename=f"{Path(filename).stem}{ext}",
            content_type=content_type,
        )
        transport = self._ensure_transport(self._ensure_bot())
        payload_text = await transport.upload(url=url, data=form)
        try:
            return json.loads(payload_text)
        except json.JSONDecodeError:
            return {"text": payload_text}

    def _ensure_transport(self, bot: Any) -> MaxApiTransport:
        if self._transport is not None:
            return self._transport
        config = TransportConfig.from_default_connection(bot.default_connection)
        config.session_kwargs.setdefault(
            "connector_limit",
            getattr(bot.default_connection, "connector_limit", 100),
        )
        config.session_kwargs.setdefault(
            "connector_limit_per_host",
            getattr(bot.default_connection, "connector_limit_per_host", 30),
        )
        self._transport = MaxApiTransport(
            base_url=bot.api_url,
            headers=dict(getattr(bot, "headers", {})),
            config=config,
            session=getattr(bot, "session", None),
        )
        if self._transport.session is not None:
            bot.session = self._transport.session
            self.session = self._transport.session
        return self._transport

    def _bind_bot(self, *, bot: Any, payload: Any) -> None:
        if payload is None:
            return
        if hasattr(payload, "bind_bot"):
            payload.bind_bot(bot)
        if hasattr(payload, "message") and getattr(payload, "message") is not None:
            message = getattr(payload, "message")
            if hasattr(message, "bind_bot"):
                message.bind_bot(bot)
        if hasattr(payload, "messages"):
            for message in getattr(payload, "messages") or []:
                if hasattr(message, "bind_bot"):
                    message.bind_bot(bot)
        if hasattr(payload, "updates"):
            for update in getattr(payload, "updates") or []:
                message = getattr(update, "message", None)
                if message is not None and hasattr(message, "bind_bot"):
                    message.bind_bot(bot)
                callback = getattr(update, "callback", None)
                if callback is not None and getattr(callback, "message", None) is not None:
                    callback_message = callback.message
                    if hasattr(callback_message, "bind_bot"):
                        callback_message.bind_bot(bot)
