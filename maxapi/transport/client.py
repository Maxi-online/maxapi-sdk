from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any

from aiohttp import (
    ClientConnectionError,
    ClientPayloadError,
    ClientResponse,
    ClientSession,
    ContentTypeError,
    FormData,
    TCPConnector,
)

from ..exceptions.max import InvalidToken, MaxApiError, MaxConnection
from .config import TransportConfig
from .errors import RateLimitExceededError, ResponseDecodeError, ServerResponseError


@dataclass(slots=True)
class TransportResult:
    raw: Any
    parsed: Any
    status: int
    headers: dict[str, str]


class MaxApiTransport:
    """Надёжный HTTP-клиент для MAX API."""

    def __init__(
        self,
        *,
        base_url: str,
        headers: dict[str, str] | None = None,
        config: TransportConfig,
        session: ClientSession | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = dict(headers or {})
        self._config = config
        self._session = session
        self._owns_session = False

    @property
    def session(self) -> ClientSession | None:
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()

    async def request(
        self,
        *,
        method: str,
        path: str,
        model: Any = None,
        **kwargs: Any,
    ) -> TransportResult:
        retry_policy = self._config.retry_policy
        normalized_method = method.upper()
        last_error: Exception | None = None

        for attempt in range(1, retry_policy.attempts + 1):
            response: ClientResponse | None = None
            try:
                session = await self._ensure_session()
                url = path if path.startswith("http") else f"{self._base_url}{path}"
                response = await session.request(method=normalized_method, url=url, **kwargs)
                return await self._handle_response(response=response, model=model)
            except InvalidToken:
                raise
            except RateLimitExceededError as exc:
                last_error = exc
                if attempt >= retry_policy.attempts:
                    raise MaxApiError(
                        code=exc.status,
                        raw=exc.payload,
                        message=exc.message,
                        headers=exc.headers,
                    ) from exc
                await asyncio.sleep(
                    retry_policy.delay_for_attempt(attempt, retry_after=exc.retry_after)
                )
            except ServerResponseError as exc:
                last_error = exc
                if attempt >= retry_policy.attempts:
                    raise MaxApiError(
                        code=exc.status,
                        raw=exc.payload,
                        message=exc.message,
                        headers=exc.headers,
                    ) from exc
                await asyncio.sleep(retry_policy.delay_for_attempt(attempt))
            except (ClientConnectionError, ClientPayloadError, asyncio.TimeoutError) as exc:
                last_error = exc
                if attempt >= retry_policy.attempts or not retry_policy.allows(normalized_method):
                    raise MaxConnection(f"Ошибка при отправке запроса: {exc}") from exc
                await asyncio.sleep(retry_policy.delay_for_attempt(attempt))
            finally:
                if response is not None and not response.closed:
                    response.release()

        if last_error is not None:
            raise MaxConnection(f"Ошибка при отправке запроса: {last_error}") from last_error
        raise MaxConnection("Ошибка при отправке запроса: неизвестная ошибка")

    async def upload(self, *, url: str, data: FormData) -> str:
        session = await self._ensure_session(upload_mode=True)
        try:
            async with session.post(url=url, data=data) as response:
                text = await response.text()
                if response.status >= 400:
                    payload = self._try_parse_json_text(text)
                    raise MaxApiError(
                        code=response.status,
                        raw=payload,
                        message="Ошибка загрузки файла в MAX",
                        headers=dict(response.headers),
                    )
                return text
        except ClientConnectionError as exc:
            raise MaxConnection(f"Ошибка при загрузке файла: {exc}") from exc

    async def _ensure_session(self, *, upload_mode: bool = False) -> ClientSession:
        if self._session is not None and not self._session.closed:
            return self._session

        session_kwargs = dict(self._config.session_kwargs)
        session_kwargs.setdefault("timeout", self._config.timeout)
        session_kwargs.setdefault("headers", self._headers)
        session_kwargs.setdefault(
            "connector",
            TCPConnector(
                limit=session_kwargs.pop("connector_limit", 100),
                limit_per_host=session_kwargs.pop("connector_limit_per_host", 30),
            ),
        )

        if upload_mode:
            session_kwargs.pop("headers", None)

        self._session = ClientSession(**session_kwargs)
        self._owns_session = True
        return self._session

    async def _handle_response(
        self,
        *,
        response: ClientResponse,
        model: Any,
    ) -> TransportResult:
        headers = dict(response.headers)
        raw = await self._decode_response(response)

        if response.status == 401:
            raise InvalidToken("Неверный токен!", raw=raw, headers=headers)
        if response.status == 429:
            retry_after = self._extract_retry_after(headers)
            raise RateLimitExceededError(
                status=response.status,
                payload=raw,
                headers=headers,
                retry_after=retry_after,
                message="API MAX вернул 429 Too Many Requests",
            )
        if 500 <= response.status <= 599:
            raise ServerResponseError(
                status=response.status,
                payload=raw,
                headers=headers,
                message="API MAX вернул серверную ошибку",
            )
        if response.status >= 400:
            raise MaxApiError(code=response.status, raw=raw, headers=headers)

        parsed = self._parse_model(model=model, raw=raw)
        return TransportResult(raw=raw, parsed=parsed, status=response.status, headers=headers)

    async def _decode_response(self, response: ClientResponse) -> Any:
        if response.status == 204:
            return {}

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type.lower():
            try:
                return await response.json(content_type=None)
            except (ContentTypeError, json.JSONDecodeError) as exc:
                text = await response.text()
                raise ResponseDecodeError(text=text, content_type=content_type) from exc

        text = await response.text()
        return self._try_parse_json_text(text)

    def _parse_model(self, *, model: Any, raw: Any) -> Any:
        if model is None:
            return raw
        if hasattr(model, "model_validate"):
            return model.model_validate(raw)
        if hasattr(model, "parse_obj"):
            return model.parse_obj(raw)
        if callable(model):
            return model(**raw)
        return raw

    @staticmethod
    def _try_parse_json_text(text: str) -> Any:
        if not text.strip():
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}

    @staticmethod
    def _extract_retry_after(headers: dict[str, str]) -> float | None:
        retry_after = headers.get("Retry-After")
        if retry_after is None:
            return None
        try:
            return float(retry_after)
        except ValueError:
            pass
        try:
            parsed = parsedate_to_datetime(retry_after)
        except (TypeError, ValueError):
            return None
        now = parsed.tzinfo and parsed.now(parsed.tzinfo) or None
        if now is None:
            return None
        delay = (parsed - now).total_seconds()
        if delay <= 0:
            return None
        return delay
