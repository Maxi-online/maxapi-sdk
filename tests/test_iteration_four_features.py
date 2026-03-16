from __future__ import annotations

from pathlib import Path

from maxapi import Bot, Dispatcher, MemoryStorage, TextStartsWith
from maxapi.callback_schema import CallbackPayloadSchema
from maxapi.client.default import DefaultConnectionProperties
from maxapi.fsm import State, StateFilter, StatesGroup
from maxapi.plugins import BasePlugin
from maxapi.types import SendMessageResponse, UpdateType


class DummyBot(Bot):
    def __init__(self) -> None:
        super().__init__(
            token="token",
            default_connection=DefaultConnectionProperties(request_retries=1),
        )
        self.sent_messages: list[tuple[int | None, str | None]] = []

    async def send_message(self, **kwargs):
        self.sent_messages.append((kwargs.get("chat_id"), kwargs.get("text")))
        payload = {
            "message": {
                "message_id": "generated",
                "chat_id": kwargs.get("chat_id"),
                "body": {"text": kwargs.get("text")},
            }
        }
        return SendMessageResponse.model_validate(payload)


class FormStates(StatesGroup):
    name = State()
    confirm = State()


class AdminAction(CallbackPayloadSchema):
    prefix = "admin"
    action: str
    user_id: int


class EchoPlugin(BasePlugin):
    name = "echo"

    def setup(self, router) -> None:
        @router.message_created()
        async def echo_handler(event):
            await event.message.answer("plugin")


async def test_fsm_context_is_injected_and_state_filter_matches():
    bot = DummyBot()
    dp = Dispatcher(storage=MemoryStorage())
    seen: list[tuple[str | None, dict[str, str]]] = []

    @dp.message_created()
    async def step_one(message, state):
        if message.body.text == "/form":
            await state.set_state(FormStates.name)
            await state.update_data(step="name")
            await message.answer("Введите имя")

    @dp.message_created(StateFilter(FormStates.name) & ~TextStartsWith("/"))
    async def step_two(message, state, state_data, raw_state):
        seen.append((raw_state, state_data))
        await state.set_state(FormStates.confirm)
        await message.answer(f"Принято: {message.body.text}")

    await dp.process_update(
        {
            "update_type": UpdateType.MESSAGE_CREATED.value,
            "message": {
                "message_id": "m1",
                "chat_id": 101,
                "sender": {"user_id": 5},
                "body": {"text": "/form"},
            },
        },
        bot=bot,
    )
    await dp.process_update(
        {
            "update_type": UpdateType.MESSAGE_CREATED.value,
            "message": {
                "message_id": "m2",
                "chat_id": 101,
                "sender": {"user_id": 5},
                "body": {"text": "Макс"},
            },
        },
        bot=bot,
    )

    assert bot.sent_messages == [(101, "Введите имя"), (101, "Принято: Макс")]
    assert seen == [("FormStates:name", {"step": "name"})]


async def test_callback_payload_schema_pack_unpack_and_filter_work():
    bot = DummyBot()
    dp = Dispatcher()
    values: list[tuple[str, int]] = []
    payload = AdminAction(action="ban", user_id=42).pack()

    @dp.message_callback(AdminAction.filter(action="ban"))
    async def handle_callback(callback_event, callback_payload_text):
        parsed = callback_event.unpack(AdminAction)
        values.append((callback_payload_text, parsed.user_id))

    await dp.process_update(
        {
            "update_type": UpdateType.MESSAGE_CALLBACK.value,
            "callback": {
                "callback_id": "cb1",
                "payload": payload,
                "message": {
                    "message_id": "m1",
                    "chat_id": 77,
                    "body": {"text": "moderation"},
                },
            },
        },
        bot=bot,
    )

    assert values == [(payload, 42)]
    assert AdminAction.unpack(payload).action == "ban"


async def test_plugin_can_register_handlers():
    bot = DummyBot()
    dp = Dispatcher()
    plugin = dp.include_plugin(EchoPlugin())

    await dp.process_update(
        {
            "update_type": UpdateType.MESSAGE_CREATED.value,
            "message": {
                "message_id": "m1",
                "chat_id": 88,
                "body": {"text": "hello"},
            },
        },
        bot=bot,
    )

    assert plugin.name == "echo"
    assert bot.sent_messages == [(88, "plugin")]


def test_publish_workflow_exists_and_uses_trusted_publishing():
    workflow_path = Path(".github/workflows/publish.yml")
    content = workflow_path.read_text(encoding="utf-8")

    assert "pypa/gh-action-pypi-publish@release/v1" in content
    assert "id-token: write" in content
    assert "softprops/action-gh-release@v2" in content
