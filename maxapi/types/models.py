from __future__ import annotations

from enum import Enum
from typing import Any

from ..builders import normalize_attachments

from pydantic import Field, PrivateAttr

from .base import ApiModel


class TextFormat(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"


class SenderAction(str, Enum):
    TYPING_ON = "typing_on"
    SENDING_PHOTO = "sending_photo"
    SENDING_VIDEO = "sending_video"
    SENDING_AUDIO = "sending_audio"
    SENDING_FILE = "sending_file"
    MARK_SEEN = "mark_seen"


class UploadType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"


class UpdateType(str, Enum):
    MESSAGE_CREATED = "message_created"
    MESSAGE_CALLBACK = "message_callback"
    MESSAGE_EDITED = "message_edited"
    MESSAGE_REMOVED = "message_removed"
    BOT_STARTED = "bot_started"
    BOT_ADDED = "bot_added"
    BOT_REMOVED = "bot_removed"
    BOT_STOPPED = "bot_stopped"
    USER_ADDED = "user_added"
    USER_REMOVED = "user_removed"
    CHAT_TITLE_CHANGED = "chat_title_changed"
    DIALOG_CLEARED = "dialog_cleared"
    DIALOG_MUTED = "dialog_muted"
    DIALOG_UNMUTED = "dialog_unmuted"
    DIALOG_REMOVED = "dialog_removed"
    RAW_API_RESPONSE = "raw_api_response"


class Image(ApiModel):
    url: str | None = None
    token: str | None = None


class BotCommand(ApiModel):
    name: str
    description: str | None = None


class User(ApiModel):
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    is_bot: bool | None = None
    last_activity_time: int | None = None
    name: str | None = None
    description: str | None = None
    avatar_url: str | None = None
    full_avatar_url: str | None = None
    commands: list[BotCommand] | None = None


class Recipient(ApiModel):
    chat_id: int | None = None
    user_id: int | None = None
    type: str | None = None


class LinkedMessage(ApiModel):
    type: str | None = None
    message: dict[str, Any] | None = None


class MessageBody(ApiModel):
    text: str | None = None
    attachments: list[dict[str, Any]] | None = None
    link: dict[str, Any] | None = None
    notify: bool | None = None
    format: TextFormat | None = Field(default=None, alias="format")


class Message(ApiModel):
    message_id: str | None = None
    sender: User | None = None
    recipient: Recipient | None = None
    timestamp: int | None = None
    link: LinkedMessage | None = None
    body: MessageBody | None = None
    stat: dict[str, Any] | None = None
    url: str | None = None
    chat_id: int | None = None
    callback_id: str | None = None
    update_type: str | None = None
    _bot: Any = PrivateAttr(default=None)

    def bind_bot(self, bot: Any) -> "Message":
        self._bot = bot
        return self

    async def answer(
        self,
        text: str,
        *,
        format: TextFormat | None = None,
        notify: bool | None = None,
        attachments: list[dict[str, Any]] | None = None,
        keyboard: Any | None = None,
        disable_link_preview: bool | None = None,
    ) -> "SendMessageResponse":
        if self._bot is None:
            raise RuntimeError("Сообщение не связано с экземпляром Bot.")
        target_chat_id = self.chat_id
        if target_chat_id is None and self.recipient is not None:
            target_chat_id = self.recipient.chat_id
        target_user_id = None
        if target_chat_id is None and self.recipient is not None:
            target_user_id = self.recipient.user_id
        return await self._bot.send_message(
            chat_id=target_chat_id,
            user_id=target_user_id,
            text=text,
            format=format,
            notify=notify,
            attachments=normalize_attachments(attachments, keyboard=keyboard),
            disable_link_preview=disable_link_preview,
        )

    async def reply(
        self,
        text: str,
        *,
        format: TextFormat | None = None,
        notify: bool | None = None,
        attachments: list[dict[str, Any]] | None = None,
        keyboard: Any | None = None,
        disable_link_preview: bool | None = None,
    ) -> "SendMessageResponse":
        return await self.answer(
            text=text,
            format=format,
            notify=notify,
            attachments=attachments,
            keyboard=keyboard,
            disable_link_preview=disable_link_preview,
        )


class MessageList(ApiModel):
    messages: list[Message]


class SendMessageResponse(ApiModel):
    message: Message


class EditMessageResponse(ApiModel):
    message: Message


class SuccessResponse(ApiModel):
    success: bool
    message: str | None = None


class VideoInfo(ApiModel):
    url: str | None = None
    token: str | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None
    preview_url: str | None = None


class Chat(ApiModel):
    chat_id: int
    type: str | None = None
    status: str | None = None
    title: str | None = None
    icon: Image | None = None
    last_event_time: int | None = None
    participants_count: int | None = None
    owner_id: int | None = None
    participants: dict[str, Any] | None = None
    is_public: bool | None = None
    link: str | None = None
    description: str | None = None
    dialog_with_user: User | None = None
    chat_message_id: str | None = None
    pinned_message: Message | None = None


class ChatsPage(ApiModel):
    chats: list[Chat]
    marker: int | None = None


class ChatMember(User):
    last_access_time: int | None = None
    is_owner: bool | None = None
    is_admin: bool | None = None
    join_time: int | None = None
    permissions: list[str] | None = None
    alias: str | None = None


class ChatAdmin(ApiModel):
    user_id: int
    permissions: list[str] | None = None
    alias: str | None = None


class MembersPage(ApiModel):
    members: list[ChatMember]
    marker: int | None = None


class Subscription(ApiModel):
    url: str
    update_types: list[str] | None = None
    secret: str | None = None


class SubscriptionsPage(ApiModel):
    subscriptions: list[Subscription]


class UploadResponse(ApiModel):
    url: str
    token: str | None = None


class CallbackPayload(ApiModel):
    callback_id: str | None = None
    payload: Any | None = None
    user: User | None = None
    message: Message | None = None


class Update(ApiModel):
    update_type: UpdateType | str
    timestamp: int | None = None
    message: Message | None = None
    callback: CallbackPayload | None = None
    callback_id: str | None = None
    user_locale: str | None = None
    chat_id: int | None = None
    user_id: int | None = None


class UpdatesPage(ApiModel):
    updates: list[Update]
    marker: int | None = None


class SendMessageRequest(ApiModel):
    text: str | None = None
    attachments: list[dict[str, Any]] | None = None
    link: dict[str, Any] | None = None
    notify: bool | None = None
    format: TextFormat | None = Field(default=None, alias="format")


class EditMessageRequest(ApiModel):
    message_id: str
    text: str | None = None
    attachments: list[dict[str, Any]] | None = None
    link: dict[str, Any] | None = None
    notify: bool | None = None
    format: TextFormat | None = Field(default=None, alias="format")


class WebhookRequest(ApiModel):
    url: str
    update_types: list[UpdateType | str] | None = None
    secret: str | None = None


class PinMessageRequest(ApiModel):
    message_id: str
    notify: bool | None = True


class AddMembersRequest(ApiModel):
    user_ids: list[int]


class AddAdminsRequest(ApiModel):
    admins: list[ChatAdmin]
    marker: int | None = None


class AnswerCallbackRequest(ApiModel):
    notification: str | None = None
    message: MessageBody | None = None
