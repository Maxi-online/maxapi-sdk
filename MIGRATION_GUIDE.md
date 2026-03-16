# Migration guide: 0.11.x -> 0.12.0

## Что появилось

- FSM для сценариев с несколькими шагами;
- storage abstraction и `MemoryStorage`;
- plugin API для модульного подключения функциональности;
- structured callback payload parsing;
- release automation для GitHub Releases и PyPI.

## FSM

Было:

```python
dp = Dispatcher()
```

Стало:

```python
from maxapi import Dispatcher, MemoryStorage


dp = Dispatcher(storage=MemoryStorage())
```

Использование state в handler:

```python
from maxapi import State, StateFilter, StatesGroup


class Form(StatesGroup):
    name = State()
    confirm = State()


@dp.message_created()
async def start_form(message, state):
    if message.body.text == "/form":
        await state.set_state(Form.name)
        await state.update_data(step="name")


@dp.message_created(StateFilter(Form.name))
async def save_name(message, state, state_data):
    await state.update_data(name=message.body.text)
```

## Plugin API

```python
from maxapi import BasePlugin


class EchoPlugin(BasePlugin):
    name = "echo"

    def setup(self, router) -> None:
        @router.message_created()
        async def echo_handler(message):
            await message.answer("plugin")


dp.include_plugin(EchoPlugin())
```

## Structured callback payload

Было:

```python
@dp.message_callback(CallbackData("approve"))
async def handle(event):
    ...
```

Стало:

```python
from maxapi import CallbackPayloadSchema


class AdminAction(CallbackPayloadSchema):
    prefix = "admin"
    action: str
    user_id: int


@dp.message_callback(AdminAction.filter(action="ban"))
async def handle(callback_event):
    parsed = callback_event.unpack(AdminAction)
    print(parsed.user_id)
```

## Новые внедряемые аргументы handler

Теперь, кроме уже существующих `bot`, `dispatcher`, `router`, `message`, `callback`, `chat_id`, `user_id`, доступны:

- `state` / `fsm_context`
- `raw_state`
- `state_data`
- `callback_payload`
- `callback_payload_text`
- `callback_payload_dict`

## Release automation

Для публикации релиза достаточно:

1. обновить версию в `pyproject.toml` и `CHANGELOG.md`;
2. создать git tag формата `v0.12.0`;
3. push-нуть ветку и tag в GitHub;
4. убедиться, что PyPI Trusted Publisher настроен для репозитория.
