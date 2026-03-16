from __future__ import annotations

from fastapi.testclient import TestClient

from maxapi import Bot, Command, Dispatcher
from maxapi.client.default import DefaultConnectionProperties
from maxapi.runners import PollingRunner
from maxapi.types import MessageBody, SendMessageResponse, UpdateType, UpdatesPage


class DummyBot(Bot):
    def __init__(self):
        super().__init__(
            token="token",
            default_connection=DefaultConnectionProperties(request_retries=1),
        )
        self.sent_messages: list[tuple[int | None, int | None, str | None]] = []
        self.callback_answers: list[str] = []
        self._updates_pages: list[UpdatesPage] = []

    async def send_message(self, **kwargs):
        self.sent_messages.append(
            (kwargs.get("chat_id"), kwargs.get("user_id"), kwargs.get("text"))
        )
        payload = {
            "message": {
                "message_id": "generated",
                "chat_id": kwargs.get("chat_id"),
                "body": {"text": kwargs.get("text")},
            }
        }
        return SendMessageResponse.model_validate(payload)

    async def answer_callback(self, callback_id: str, **kwargs):
        del kwargs
        self.callback_answers.append(callback_id)
        return {"success": True}

    async def get_subscriptions(self):
        return type("Subscriptions", (), {"subscriptions": []})()

    async def get_updates(self, **kwargs):
        del kwargs
        return self._updates_pages.pop(0)


async def test_dispatcher_command_filter_answers_message():
    bot = DummyBot()
    dp = Dispatcher()

    @dp.message_created(Command("start"))
    async def handle_start(event):
        await event.message.answer("pong")

    payload = {
        "update_type": UpdateType.MESSAGE_CREATED.value,
        "message": {
            "message_id": "m1",
            "chat_id": 123,
            "body": {"text": "/start"},
        },
    }

    await dp.process_update(payload, bot=bot)

    assert bot.sent_messages == [(123, None, "pong")]


async def test_polling_runner_advances_marker_and_dispatches_updates():
    bot = DummyBot()
    dp = Dispatcher()
    seen_messages: list[str] = []

    @dp.message_created()
    async def handle_message(event):
        seen_messages.append(event.message.body.text)

    bot._updates_pages = [
        UpdatesPage.model_validate(
            {
                "updates": [
                    {
                        "update_type": UpdateType.MESSAGE_CREATED.value,
                        "message": {
                            "message_id": "m1",
                            "chat_id": 1,
                            "body": {"text": "hello"},
                        },
                    }
                ],
                "marker": 77,
            }
        )
    ]

    runner = PollingRunner(bot=bot, dispatcher=dp)
    await runner.run_once()

    assert seen_messages == ["hello"]
    assert bot.marker_updates == 77


def test_webhook_runner_validates_secret_and_dispatches():
    bot = DummyBot()
    dp = Dispatcher()

    @dp.message_created()
    async def handle_message(event):
        await event.message.answer("from webhook")

    app = dp.create_webhook_app(bot=bot, path="/hook", secret="abc123")
    client = TestClient(app)

    ok_response = client.post(
        "/hook",
        headers={"X-Max-Bot-Api-Secret": "abc123"},
        json={
            "update_type": UpdateType.MESSAGE_CREATED.value,
            "message": {
                "message_id": "m1",
                "chat_id": 456,
                "body": {"text": "hello"},
            },
        },
    )
    assert ok_response.status_code == 200
    assert bot.sent_messages == [(456, None, "from webhook")]

    forbidden_response = client.post(
        "/hook",
        headers={"X-Max-Bot-Api-Secret": "wrong"},
        json={
            "update_type": UpdateType.MESSAGE_CREATED.value,
            "message": {
                "message_id": "m2",
                "chat_id": 456,
                "body": {"text": "hello"},
            },
        },
    )
    assert forbidden_response.status_code == 403
