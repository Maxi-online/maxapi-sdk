# maxapi-sdk 0.12.1

Python SDK для MAX Messenger Bot API.

Пакет публикуется в PyPI как `maxapi-sdk`, а в коде импортируется как `maxapi`.

## Что есть в пакете

- typed Bot API client для методов MAX;
- отдельные runtime-классы `PollingRunner` и `WebhookRunner`;
- transport-слой с retry/backoff и поддержкой `Retry-After`;
- `Router` и `Dispatcher` с middleware и инъекцией зависимостей в handlers;
- composable filters с операторами `&`, `|`, `~`;
- `InlineKeyboardBuilder` и media helpers для upload/send flow;
- FSM: `State`, `StatesGroup`, `FSMContext`, `MemoryStorage`, `StateFilter`;
- plugin API для модульного подключения функциональности;
- structured callback payload parsing через `CallbackPayloadSchema`;
- migration layer для старого стиля кода;
- GitHub Actions для тестов, сборки, GitHub Releases и публикации в PyPI.

## Установка

```bash
pip install maxapi-sdk
pip install "maxapi-sdk[webhook]"
```

## Установка для разработки

```bash
pip install -e .
pip install -e .[webhook]
pip install -e .[dev]
```

## Быстрый старт: polling

```python
import asyncio
import os

from maxapi import Bot, Command, Dispatcher, InlineKeyboardBuilder


bot = Bot(token=os.environ["MAX_BOT_TOKEN"])
dp = Dispatcher()


@dp.message_created(Command("start"))
async def handle_start(event):
    keyboard = (
        InlineKeyboardBuilder()
        .callback("Подтвердить", "confirm")
        .link("Документация", "https://dev.max.ru/docs-api")
        .adjust(1, 1)
    )
    await event.message.answer("Привет из maxapi 0.12.1", keyboard=keyboard)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

## FSM

```python
import asyncio
import os

from maxapi import Bot, Dispatcher, MemoryStorage, State, StateFilter, StatesGroup


class Registration(StatesGroup):
    name = State()
    confirm = State()


bot = Bot(token=os.environ["MAX_BOT_TOKEN"])
dp = Dispatcher(storage=MemoryStorage())


@dp.message_created()
async def start_form(message, state):
    if message.body.text == "/form":
        await state.set_state(Registration.name)
        await state.update_data(step="name")
        await message.answer("Введите имя")


@dp.message_created(StateFilter(Registration.name))
async def save_name(message, state, state_data):
    await state.update_data(name=message.body.text)
    data = await state.get_data()
    await state.set_state(Registration.confirm)
    await message.answer(f"Подтвердить имя: {data['name']}")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

## Structured callback payload

```python
from maxapi import CallbackPayloadSchema, Dispatcher


class AdminAction(CallbackPayloadSchema):
    prefix = "admin"
    action: str
    user_id: int


payload = AdminAction(action="ban", user_id=42).pack()


dp = Dispatcher()


@dp.message_callback(AdminAction.filter(action="ban"))
async def handle_ban(callback_event, callback_payload_text):
    parsed = callback_event.unpack(AdminAction)
    await callback_event.answer(notification=f"Ban for user {parsed.user_id}")
```

## Plugin API

```python
from maxapi import BasePlugin, Dispatcher


class MetricsPlugin(BasePlugin):
    name = "metrics"

    def setup(self, router) -> None:
        @router.message_created()
        async def mark_message(message, bot):
            del bot
            print(f"message_id={message.message_id}")


dp = Dispatcher()
dp.include_plugin(MetricsPlugin())
```

## Webhook

```python
import asyncio
import os

from maxapi import Bot, Dispatcher


bot = Bot(token=os.environ["MAX_BOT_TOKEN"])
dp = Dispatcher()


async def main() -> None:
    await dp.handle_webhook(
        bot=bot,
        host="0.0.0.0",
        port=8080,
        path="/webhook",
        secret=os.environ["MAX_BOT_WEBHOOK_SECRET"],
    )


if __name__ == "__main__":
    asyncio.run(main())
```

## Media helpers

```python
response = await bot.send_image(
    "/tmp/banner.png",
    chat_id=123,
    text="Готово",
    processing_wait=0.5,
    attachment_ready_retries=3,
)
```

## Migration layer

```python
from maxapi.compat import Keyboard, LegacyBot, LegacyDispatcher


bot = LegacyBot(token="token")
dp = LegacyDispatcher()
keyboard = Keyboard().callback("OK", "done").row()


@dp.message_handler()
async def legacy_handler(event):
    await bot.send_text(chat_id=event.chat_id, text="legacy", keyboard=keyboard)
```

## CI/CD

В репозитории есть два workflow:

- `.github/workflows/tests.yml` — тесты и проверка сборки пакета;
- `.github/workflows/publish.yml` — сборка артефактов, публикация в PyPI через Trusted Publishing и создание GitHub Release по тегу `v*`.

## Репозиторий

- GitHub: `https://github.com/Maxi-online/maxapi-sdk`

## Структура

- `maxapi.bot` — typed Bot API client;
- `maxapi.dispatcher` — Router/Dispatcher, middleware, handler injection;
- `maxapi.runners.polling` — long polling runtime;
- `maxapi.runners.webhook` — FastAPI/uvicorn webhook runtime;
- `maxapi.filters` — composable filters;
- `maxapi.builders` — keyboard/media builders;
- `maxapi.fsm` — FSM, storage и state filters;
- `maxapi.plugins` — plugin API;
- `maxapi.middlewares` — middleware base classes;
- `maxapi.compat` — migration layer;
- `maxapi.transport` — HTTP transport;
- `maxapi.types` — pydantic-модели.
