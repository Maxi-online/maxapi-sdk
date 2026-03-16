from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Iterable

from .builders import build_uploaded_attachment, normalize_attachments
from .client.default import DefaultConnectionProperties
from .connection.base import BaseConnection
from .exceptions import InvalidToken, MaxApiError
from .types import (
    AddAdminsRequest,
    AddMembersRequest,
    AnswerCallbackRequest,
    Chat,
    ChatsPage,
    ChatAdmin,
    EditMessageRequest,
    EditMessageResponse,
    MembersPage,
    Message,
    MessageBody,
    MessageList,
    PinMessageRequest,
    SendMessageRequest,
    SendMessageResponse,
    SenderAction,
    SubscriptionsPage,
    SuccessResponse,
    TextFormat,
    UpdateType,
    UpdatesPage,
    UploadResponse,
    UploadType,
    User,
    VideoInfo,
    WebhookRequest,
)


class Bot(BaseConnection):
    """Typed client для MAX Bot API."""

    def __init__(
        self,
        token: str | None = None,
        *,
        default_connection: DefaultConnectionProperties | None = None,
        api_url: str = "https://platform-api.max.ru",
        marker_updates: int | None = None,
        auto_check_subscriptions: bool = True,
    ) -> None:
        super().__init__()
        self.bot = self
        self.default_connection = default_connection or DefaultConnectionProperties()
        self.api_url = api_url.rstrip("/")
        self.marker_updates = marker_updates
        self.auto_check_subscriptions = auto_check_subscriptions
        self.dispatcher = None
        self._me: User | None = None
        self.__token = token or os.environ.get("MAX_BOT_TOKEN")
        if self.__token is None:
            raise InvalidToken(
                'Токен не может быть None. Укажите Bot(token="...") или MAX_BOT_TOKEN.'
            )
        self.headers: dict[str, str] = {"Authorization": self.__token}

    @property
    def me(self) -> User | None:
        return self._me

    async def close_session(self) -> None:
        if self._transport is not None:
            await self._transport.close()
        elif self.session is not None and not self.session.closed:
            await self.session.close()

    async def get_me(self) -> User:
        me = await self.request("GET", "/me", model=User)
        self._me = me
        return me

    async def get_chats(self, *, count: int | None = None, marker: int | None = None) -> ChatsPage:
        params = {"count": count, "marker": marker}
        params = {key: value for key, value in params.items() if value is not None}
        return await self.request("GET", "/chats", model=ChatsPage, params=params)

    async def get_chat(self, chat_id: int) -> Chat:
        return await self.request("GET", f"/chats/{chat_id}", model=Chat)

    async def update_chat(
        self,
        chat_id: int,
        *,
        title: str | None = None,
        icon: dict[str, Any] | None = None,
        pin: str | None = None,
        notify: bool | None = None,
    ) -> Chat:
        payload = {
            "title": title,
            "icon": icon,
            "pin": pin,
            "notify": notify,
        }
        payload = {key: value for key, value in payload.items() if value is not None}
        return await self.request("PATCH", f"/chats/{chat_id}", model=Chat, json=payload)

    async def delete_chat(self, chat_id: int) -> SuccessResponse:
        return await self.request("DELETE", f"/chats/{chat_id}", model=SuccessResponse)

    async def send_chat_action(
        self,
        chat_id: int,
        action: SenderAction = SenderAction.TYPING_ON,
    ) -> SuccessResponse:
        return await self.request(
            "POST",
            f"/chats/{chat_id}/actions",
            model=SuccessResponse,
            json={"action": action.value},
        )

    async def get_pinned_message(self, chat_id: int) -> SendMessageResponse:
        return await self.request(
            "GET",
            f"/chats/{chat_id}/pin",
            model=SendMessageResponse,
        )

    async def pin_message(
        self,
        chat_id: int,
        message_id: str,
        *,
        notify: bool | None = True,
    ) -> SuccessResponse:
        payload = PinMessageRequest(message_id=message_id, notify=notify)
        return await self.request(
            "PUT",
            f"/chats/{chat_id}/pin",
            model=SuccessResponse,
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )

    async def unpin_message(self, chat_id: int) -> SuccessResponse:
        return await self.request(
            "DELETE",
            f"/chats/{chat_id}/pin",
            model=SuccessResponse,
        )

    async def get_membership(self, chat_id: int):
        return await self.request(
            "GET",
            f"/chats/{chat_id}/members/me",
            model=Chat,
        )

    async def leave_chat(self, chat_id: int) -> SuccessResponse:
        return await self.request(
            "DELETE",
            f"/chats/{chat_id}/members/me",
            model=SuccessResponse,
        )

    async def get_chat_admins(self, chat_id: int) -> MembersPage:
        return await self.request(
            "GET",
            f"/chats/{chat_id}/members/admins",
            model=MembersPage,
        )

    async def add_chat_admins(self, chat_id: int, admins: list[ChatAdmin]) -> SuccessResponse:
        payload = AddAdminsRequest(admins=admins)
        return await self.request(
            "POST",
            f"/chats/{chat_id}/members/admins",
            model=SuccessResponse,
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )

    async def remove_chat_admin(self, chat_id: int, user_id: int) -> SuccessResponse:
        return await self.request(
            "DELETE",
            f"/chats/{chat_id}/members/admins/{user_id}",
            model=SuccessResponse,
        )

    async def get_chat_members(
        self,
        chat_id: int,
        *,
        user_ids: list[int] | None = None,
        marker: int | None = None,
        count: int | None = None,
    ) -> MembersPage:
        params = {"marker": marker, "count": count}
        if user_ids:
            params["user_ids"] = ",".join(str(value) for value in user_ids)
        params = {key: value for key, value in params.items() if value is not None}
        return await self.request(
            "GET",
            f"/chats/{chat_id}/members",
            model=MembersPage,
            params=params,
        )

    async def add_chat_members(self, chat_id: int, user_ids: list[int]) -> SuccessResponse:
        payload = AddMembersRequest(user_ids=user_ids)
        return await self.request(
            "POST",
            f"/chats/{chat_id}/members",
            model=SuccessResponse,
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )

    async def remove_chat_member(
        self,
        chat_id: int,
        user_id: int,
        *,
        block: bool | None = None,
    ) -> SuccessResponse:
        params = {"user_id": user_id, "block": block}
        params = {key: value for key, value in params.items() if value is not None}
        return await self.request(
            "DELETE",
            f"/chats/{chat_id}/members",
            model=SuccessResponse,
            params=params,
        )

    async def get_subscriptions(self) -> SubscriptionsPage:
        return await self.request("GET", "/subscriptions", model=SubscriptionsPage)

    async def set_webhook(
        self,
        url: str,
        *,
        update_types: Iterable[UpdateType | str] | None = None,
        secret: str | None = None,
    ) -> SuccessResponse:
        normalized_types = None
        if update_types is not None:
            normalized_types = [item.value if hasattr(item, "value") else item for item in update_types]
        payload = WebhookRequest(url=url, update_types=normalized_types, secret=secret)
        return await self.request(
            "POST",
            "/subscriptions",
            model=SuccessResponse,
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )

    async def delete_webhook(self, url: str | None = None) -> SuccessResponse:
        params = {"url": url} if url is not None else None
        return await self.request(
            "DELETE",
            "/subscriptions",
            model=SuccessResponse,
            params=params,
        )

    async def get_updates(
        self,
        *,
        marker: int | None = None,
        limit: int = 100,
        timeout: int = 30,
        types: Iterable[UpdateType | str] | None = None,
    ) -> UpdatesPage:
        params: dict[str, Any] = {"limit": limit, "timeout": timeout}
        if marker is not None:
            params["marker"] = marker
        if types:
            params["types"] = ",".join(item.value if hasattr(item, "value") else item for item in types)
        return await self.request("GET", "/updates", model=UpdatesPage, params=params)

    async def create_upload(self, upload_type: UploadType | str) -> UploadResponse:
        upload_value = upload_type.value if hasattr(upload_type, "value") else upload_type
        return await self.request(
            "POST",
            "/uploads",
            model=UploadResponse,
            params={"type": upload_value},
        )

    async def get_messages(
        self,
        *,
        chat_id: int | None = None,
        message_ids: list[str] | None = None,
        from_time: int | None = None,
        to_time: int | None = None,
        count: int | None = None,
    ) -> MessageList:
        params: dict[str, Any] = {}
        if chat_id is not None:
            params["chat_id"] = chat_id
        if message_ids is not None:
            params["message_ids"] = ",".join(message_ids)
        if from_time is not None:
            params["from_time"] = from_time
        if to_time is not None:
            params["to_time"] = to_time
        if count is not None:
            params["count"] = count
        return await self.request("GET", "/messages", model=MessageList, params=params)

    async def get_message(self, message_id: str) -> Message:
        return await self.request("GET", f"/messages/{message_id}", model=Message)

    async def send_message(
        self,
        *,
        chat_id: int | None = None,
        user_id: int | None = None,
        text: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
        keyboard: Any | None = None,
        link: dict[str, Any] | None = None,
        format: TextFormat | None = None,
        notify: bool | None = None,
        disable_link_preview: bool | None = None,
    ) -> SendMessageResponse:
        params = {
            "chat_id": chat_id,
            "user_id": user_id,
            "disable_link_preview": disable_link_preview,
        }
        params = {key: value for key, value in params.items() if value is not None}
        payload = SendMessageRequest(
            text=text,
            attachments=normalize_attachments(attachments, keyboard=keyboard),
            link=link,
            notify=notify,
            format=format,
        )
        return await self.request(
            "POST",
            "/messages",
            model=SendMessageResponse,
            params=params,
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )

    async def edit_message(
        self,
        *,
        message_id: str,
        text: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
        keyboard: Any | None = None,
        link: dict[str, Any] | None = None,
        format: TextFormat | None = None,
        notify: bool | None = None,
    ) -> EditMessageResponse:
        payload = EditMessageRequest(
            message_id=message_id,
            text=text,
            attachments=normalize_attachments(attachments, keyboard=keyboard),
            link=link,
            notify=notify,
            format=format,
        )
        return await self.request(
            "PUT",
            "/messages",
            model=EditMessageResponse,
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )

    async def delete_message(self, message_id: str) -> SuccessResponse:
        return await self.request(
            "DELETE",
            "/messages",
            model=SuccessResponse,
            params={"message_id": message_id},
        )

    async def get_video_info(self, message_id: str) -> VideoInfo:
        return await self.request(
            "GET",
            f"/messages/{message_id}/video",
            model=VideoInfo,
        )

    async def answer_callback(
        self,
        callback_id: str,
        *,
        notification: str | None = None,
        message: MessageBody | None = None,
        keyboard: Any | None = None,
    ) -> SuccessResponse:
        payload_message = message
        if payload_message is not None:
            payload_message = payload_message.model_copy(
                update={
                    "attachments": normalize_attachments(
                        payload_message.attachments,
                        keyboard=keyboard,
                    )
                }
            )
        elif keyboard is not None:
            payload_message = MessageBody(attachments=normalize_attachments(keyboard=keyboard))
        payload = AnswerCallbackRequest(notification=notification, message=payload_message)
        return await self.request(
            "POST",
            "/answers",
            model=SuccessResponse,
            params={"callback_id": callback_id},
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )

    async def upload_attachment(
        self,
        *,
        upload_type: UploadType | str,
        path: str | os.PathLike[str] | None = None,
        filename: str | None = None,
        buffer: bytes | None = None,
    ) -> dict[str, Any]:
        upload_response = await self.create_upload(upload_type)
        upload_value = upload_type.value if hasattr(upload_type, "value") else str(upload_type)
        if path is None and buffer is None:
            raise ValueError("Необходимо передать path или buffer для upload_attachment.")
        if path is not None:
            uploaded_payload = await self.upload_file(upload_response.url, str(path), upload_value)
        else:
            if filename is None:
                raise ValueError("Для buffer-загрузки необходимо передать filename.")
            uploaded_payload = await self.upload_file_buffer(
                filename=filename,
                url=upload_response.url,
                buffer=buffer if buffer is not None else b"",
                upload_type=upload_value,
            )
        if not isinstance(uploaded_payload, dict):
            raise TypeError("MAX upload вернул неожиданный payload; ожидался JSON-объект.")
        return build_uploaded_attachment(
            upload_type=upload_value,
            upload_response_token=upload_response.token,
            uploaded_payload=uploaded_payload,
        )

    async def upload_image(self, path: str | os.PathLike[str]) -> dict[str, Any]:
        return await self.upload_attachment(upload_type=UploadType.IMAGE, path=path)

    async def upload_video(self, path: str | os.PathLike[str]) -> dict[str, Any]:
        return await self.upload_attachment(upload_type=UploadType.VIDEO, path=path)

    async def upload_audio(self, path: str | os.PathLike[str]) -> dict[str, Any]:
        return await self.upload_attachment(upload_type=UploadType.AUDIO, path=path)

    async def upload_file_attachment(self, path: str | os.PathLike[str]) -> dict[str, Any]:
        return await self.upload_attachment(upload_type=UploadType.FILE, path=path)

    async def send_media(
        self,
        *,
        upload_type: UploadType | str,
        path: str | os.PathLike[str],
        chat_id: int | None = None,
        user_id: int | None = None,
        text: str | None = None,
        keyboard: Any | None = None,
        format: TextFormat | None = None,
        notify: bool | None = None,
        disable_link_preview: bool | None = None,
        processing_wait: float = 0.0,
        attachment_ready_retries: int = 3,
        attachment_ready_delay: float = 1.0,
        attachment_ready_backoff: float = 2.0,
    ) -> SendMessageResponse:
        attachment = await self.upload_attachment(upload_type=upload_type, path=path)
        if processing_wait > 0:
            await asyncio.sleep(processing_wait)
        return await self._send_with_attachment_retry(
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            attachments=[attachment],
            keyboard=keyboard,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            retries=attachment_ready_retries,
            retry_delay=attachment_ready_delay,
            retry_backoff=attachment_ready_backoff,
        )

    async def send_image(
        self,
        path: str | os.PathLike[str],
        *,
        chat_id: int | None = None,
        user_id: int | None = None,
        text: str | None = None,
        keyboard: Any | None = None,
        format: TextFormat | None = None,
        notify: bool | None = None,
        disable_link_preview: bool | None = None,
        processing_wait: float = 0.0,
        attachment_ready_retries: int = 3,
        attachment_ready_delay: float = 1.0,
        attachment_ready_backoff: float = 2.0,
    ) -> SendMessageResponse:
        return await self.send_media(
            upload_type=UploadType.IMAGE,
            path=path,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            keyboard=keyboard,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            processing_wait=processing_wait,
            attachment_ready_retries=attachment_ready_retries,
            attachment_ready_delay=attachment_ready_delay,
            attachment_ready_backoff=attachment_ready_backoff,
        )

    async def send_video(
        self,
        path: str | os.PathLike[str],
        *,
        chat_id: int | None = None,
        user_id: int | None = None,
        text: str | None = None,
        keyboard: Any | None = None,
        format: TextFormat | None = None,
        notify: bool | None = None,
        disable_link_preview: bool | None = None,
        processing_wait: float = 0.0,
        attachment_ready_retries: int = 3,
        attachment_ready_delay: float = 1.0,
        attachment_ready_backoff: float = 2.0,
    ) -> SendMessageResponse:
        return await self.send_media(
            upload_type=UploadType.VIDEO,
            path=path,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            keyboard=keyboard,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            processing_wait=processing_wait,
            attachment_ready_retries=attachment_ready_retries,
            attachment_ready_delay=attachment_ready_delay,
            attachment_ready_backoff=attachment_ready_backoff,
        )

    async def send_audio(
        self,
        path: str | os.PathLike[str],
        *,
        chat_id: int | None = None,
        user_id: int | None = None,
        text: str | None = None,
        keyboard: Any | None = None,
        format: TextFormat | None = None,
        notify: bool | None = None,
        disable_link_preview: bool | None = None,
        processing_wait: float = 0.0,
        attachment_ready_retries: int = 3,
        attachment_ready_delay: float = 1.0,
        attachment_ready_backoff: float = 2.0,
    ) -> SendMessageResponse:
        return await self.send_media(
            upload_type=UploadType.AUDIO,
            path=path,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            keyboard=keyboard,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            processing_wait=processing_wait,
            attachment_ready_retries=attachment_ready_retries,
            attachment_ready_delay=attachment_ready_delay,
            attachment_ready_backoff=attachment_ready_backoff,
        )

    async def send_file(
        self,
        path: str | os.PathLike[str],
        *,
        chat_id: int | None = None,
        user_id: int | None = None,
        text: str | None = None,
        keyboard: Any | None = None,
        format: TextFormat | None = None,
        notify: bool | None = None,
        disable_link_preview: bool | None = None,
        processing_wait: float = 0.0,
        attachment_ready_retries: int = 3,
        attachment_ready_delay: float = 1.0,
        attachment_ready_backoff: float = 2.0,
    ) -> SendMessageResponse:
        return await self.send_media(
            upload_type=UploadType.FILE,
            path=path,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            keyboard=keyboard,
            format=format,
            notify=notify,
            disable_link_preview=disable_link_preview,
            processing_wait=processing_wait,
            attachment_ready_retries=attachment_ready_retries,
            attachment_ready_delay=attachment_ready_delay,
            attachment_ready_backoff=attachment_ready_backoff,
        )

    async def send_text(self, *args: Any, **kwargs: Any) -> SendMessageResponse:
        return await self.send_message(*args, **kwargs)

    async def edit_text(self, *args: Any, **kwargs: Any) -> EditMessageResponse:
        return await self.edit_message(*args, **kwargs)

    async def delete(self, message_id: str) -> SuccessResponse:
        return await self.delete_message(message_id)

    async def answer_callback_query(self, callback_id: str, **kwargs: Any) -> SuccessResponse:
        return await self.answer_callback(callback_id, **kwargs)

    async def _send_with_attachment_retry(
        self,
        *,
        chat_id: int | None,
        user_id: int | None,
        text: str | None,
        attachments: list[dict[str, Any]] | None,
        keyboard: Any | None,
        format: TextFormat | None,
        notify: bool | None,
        disable_link_preview: bool | None,
        retries: int,
        retry_delay: float,
        retry_backoff: float,
    ) -> SendMessageResponse:
        attempt = 0
        current_delay = retry_delay
        while True:
            try:
                return await self.send_message(
                    chat_id=chat_id,
                    user_id=user_id,
                    text=text,
                    attachments=attachments,
                    keyboard=keyboard,
                    format=format,
                    notify=notify,
                    disable_link_preview=disable_link_preview,
                )
            except MaxApiError as exc:
                if not self._is_attachment_not_ready(exc) or attempt >= retries:
                    raise
                attempt += 1
                await asyncio.sleep(current_delay)
                current_delay *= max(retry_backoff, 1.0)

    @staticmethod
    def _is_attachment_not_ready(exc: MaxApiError) -> bool:
        raw = exc.raw if isinstance(exc.raw, dict) else {}
        return raw.get("code") == "attachment.not.ready"
