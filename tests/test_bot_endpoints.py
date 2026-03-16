from __future__ import annotations

from maxapi import Bot
from maxapi.client.default import DefaultConnectionProperties
from maxapi.types import SenderAction, TextFormat, UploadType


class RecorderBot(Bot):
    def __init__(self):
        super().__init__(
            token="token",
            default_connection=DefaultConnectionProperties(request_retries=1),
        )
        self.calls = []

    async def request(self, method, path, model=None, *, is_return_raw=False, **kwargs):
        del model, is_return_raw
        self.calls.append((method, path, kwargs))
        return {"ok": True}


async def test_send_message_uses_messages_endpoint():
    bot = RecorderBot()
    await bot.send_message(chat_id=10, text="hello", format=TextFormat.HTML)
    method, path, kwargs = bot.calls[0]
    assert method == "POST"
    assert path == "/messages"
    assert kwargs["params"]["chat_id"] == 10
    assert kwargs["json"]["text"] == "hello"
    assert kwargs["json"]["format"] == TextFormat.HTML


async def test_send_chat_action_uses_actions_endpoint():
    bot = RecorderBot()
    await bot.send_chat_action(99, SenderAction.MARK_SEEN)
    method, path, kwargs = bot.calls[0]
    assert method == "POST"
    assert path == "/chats/99/actions"
    assert kwargs["json"]["action"] == SenderAction.MARK_SEEN.value


async def test_create_upload_uses_uploads_endpoint():
    bot = RecorderBot()
    await bot.create_upload(UploadType.IMAGE)
    method, path, kwargs = bot.calls[0]
    assert method == "POST"
    assert path == "/uploads"
    assert kwargs["params"]["type"] == UploadType.IMAGE.value
