from __future__ import annotations

from pathlib import Path

from maxapi import Bot, Dispatcher, InlineKeyboardBuilder, TextContains
from maxapi.builders import file_attachment
from maxapi.client.default import DefaultConnectionProperties
from maxapi.compat import Keyboard, LegacyBot, LegacyDispatcher
from maxapi.exceptions import MaxApiError
from maxapi.filters import CallbackData, ChatId, HasAttachments
from maxapi.middlewares import BaseMiddleware
from maxapi.types import SendMessageResponse, UpdateType, UploadResponse


class RecorderBot(Bot):
    def __init__(self):
        super().__init__(
            token="token",
            default_connection=DefaultConnectionProperties(request_retries=1),
        )
        self.calls = []
        self.upload_urls: list[str] = []
        self.upload_paths: list[str] = []
        self.failures_before_send = 0

    async def request(self, method, path, model=None, *, is_return_raw=False, **kwargs):
        del model, is_return_raw
        self.calls.append((method, path, kwargs))
        if path == "/uploads":
            return UploadResponse(url="https://upload.example", token="seed-token")
        if path == "/messages":
            if self.failures_before_send > 0:
                self.failures_before_send -= 1
                raise MaxApiError(
                    code=400,
                    raw={
                        "code": "attachment.not.ready",
                        "message": "Key: errors.process.attachment.file.not.processed",
                    },
                )
            return SendMessageResponse.model_validate(
                {
                    "message": {
                        "message_id": "sent-1",
                        "chat_id": kwargs.get("params", {}).get("chat_id"),
                        "body": kwargs.get("json", {}),
                    }
                }
            )
        return {"ok": True}

    async def upload_file(self, url: str, path: str, upload_type: str):
        self.upload_urls.append(url)
        self.upload_paths.append(path)
        return {"url": f"cdn://{upload_type}/{Path(path).name}"}


class CounterMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        data["counter"] = data.get("counter", 0) + 1
        return await handler(event, data)


async def test_middleware_and_injection_work_together():
    bot = RecorderBot()
    dp = Dispatcher()
    dp.use(CounterMiddleware())
    values = []

    @dp.message_created(TextContains("hello") & ChatId(1001))
    async def handler(event, bot, counter, message):
        values.append((event.chat_id, bot is not None, counter, message.body.text))

    payload = {
        "update_type": UpdateType.MESSAGE_CREATED.value,
        "message": {
            "message_id": "m1",
            "chat_id": 1001,
            "body": {"text": "hello max"},
        },
    }

    await dp.process_update(payload, bot=bot)

    assert values == [(1001, True, 1, "hello max")]


async def test_inline_keyboard_builder_is_added_to_attachments():
    bot = RecorderBot()
    keyboard = InlineKeyboardBuilder().callback("Нажми", "payload-1").row()

    await bot.send_message(chat_id=10, text="hi", keyboard=keyboard)

    _, path, kwargs = bot.calls[-1]
    assert path == "/messages"
    assert kwargs["json"]["attachments"][0]["type"] == "inline_keyboard"
    assert kwargs["json"]["attachments"][0]["payload"]["buttons"][0][0]["type"] == "callback"


async def test_send_media_retries_when_attachment_is_not_ready(tmp_path):
    bot = RecorderBot()
    bot.failures_before_send = 1
    file_path = tmp_path / "report.txt"
    file_path.write_text("payload", encoding="utf-8")

    await bot.send_file(
        file_path,
        chat_id=77,
        text="with file",
        attachment_ready_retries=2,
        attachment_ready_delay=0.01,
    )

    message_calls = [item for item in bot.calls if item[1] == "/messages"]
    assert len(message_calls) == 2
    assert bot.upload_paths == [str(file_path)]
    sent_payload = message_calls[-1][2]["json"]
    assert sent_payload["attachments"][0]["type"] == "file"
    assert sent_payload["attachments"][0]["payload"]["token"] == "seed-token"


async def test_compat_exports_and_aliases_work():
    legacy_bot = LegacyBot(token="token")
    legacy_dispatcher = LegacyDispatcher()
    keyboard = Keyboard().callback("OK", "done").row()

    assert isinstance(legacy_bot, Bot)
    assert isinstance(legacy_dispatcher, Dispatcher)
    assert keyboard.as_attachment()["type"] == "inline_keyboard"


async def test_callback_data_and_has_attachments_filters():
    bot = RecorderBot()
    dp = Dispatcher()
    matched = []

    @dp.message_callback(CallbackData("approve"))
    async def callback_handler(event):
        matched.append(event.callback_id)

    @dp.message_created(HasAttachments())
    async def attachment_handler(event):
        matched.append(event.message.message_id)

    await dp.process_update(
        {
            "update_type": UpdateType.MESSAGE_CALLBACK.value,
            "callback": {
                "callback_id": "cb1",
                "payload": {"payload": "approve"},
                "message": {
                    "message_id": "callback-message",
                    "chat_id": 12,
                    "body": {"text": "callback"},
                },
            },
        },
        bot=bot,
    )
    await dp.process_update(
        {
            "update_type": UpdateType.MESSAGE_CREATED.value,
            "message": {
                "message_id": "m-attach",
                "chat_id": 12,
                "body": {
                    "text": "doc",
                    "attachments": [file_attachment(token="abc")],
                },
            },
        },
        bot=bot,
    )

    assert matched == ["cb1", "m-attach"]
