# maxapi-sdk 0.13.0

`maxapi-sdk` is a production-ready Python SDK for the MAX Messenger Bot API.

The package is designed for teams that need a reliable foundation for bot development and operations: typed API access, resilient transport, polling and webhook runtimes, routing, middleware, FSM, plugin support, callback handling, and first-class media workflows.

## Highlights

- typed Bot API client for core MAX endpoints;
- resilient transport with retries, backoff, and `Retry-After` support;
- dedicated polling and webhook runtimes;
- routing, middleware, composable filters, and dependency injection;
- FSM primitives with in-memory storage;
- plugin API for modular bot extensions;
- structured callback payload parsing;
- first-class media support for images, audio, voice, video, and files;
- typed attachment helpers for outbound and inbound media handling;
- GitHub Actions for test, build, and release automation.

## Installation

```bash
pip install maxapi-sdk
pip install maxapi-sdk[webhook]
pip install maxapi-sdk[dev]
```

## Quick start

```python
import asyncio
import os

from maxapi import Bot, Command, Dispatcher


bot = Bot(token=os.environ["MAX_BOT_TOKEN"])
dispatcher = Dispatcher()


@dispatcher.message_created(Command("start"))
async def handle_start(event):
    await event.message.answer("Bot is running")


async def main() -> None:
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

## Media workflows

```python
from maxapi import Bot


async def send_media(bot: Bot) -> None:
    await bot.send_image("./assets/banner.png", chat_id=1001, text="Preview")
    await bot.send_voice(
        chat_id=1001,
        filename="voice.ogg",
        buffer=b"binary-audio-data",
        text="Voice update",
    )
    await bot.send_file("./reports/report.pdf", chat_id=1001, text="Report")
```

The SDK supports file path, bytes buffer, and stream-based uploads. Incoming attachments are exposed through typed accessors such as `message.images`, `message.audios`, `message.voices`, `message.videos`, and `message.files`.

## Webhook runtime

```python
import asyncio
import os

from maxapi import Bot, Dispatcher


bot = Bot(token=os.environ["MAX_BOT_TOKEN"])
dispatcher = Dispatcher()


async def main() -> None:
    await dispatcher.handle_webhook(
        bot=bot,
        host="0.0.0.0",
        port=8080,
        path="/webhook",
        secret=os.environ["MAX_BOT_WEBHOOK_SECRET"],
    )


if __name__ == "__main__":
    asyncio.run(main())
```

## FSM example

```python
from maxapi import Dispatcher, MemoryStorage, State, StateFilter, StatesGroup


class Registration(StatesGroup):
    name = State()
    confirm = State()


dispatcher = Dispatcher(storage=MemoryStorage())


@dispatcher.message_created(StateFilter(Registration.name))
async def handle_name(message, state):
    await state.update_data(name=message.body.text)
    await state.set_state(Registration.confirm)
    await message.answer("Please confirm the entered name")
```

## Packaging and release

The repository includes CI workflows for tests, package build validation, GitHub Releases, and PyPI publication via Trusted Publishing.

## Compatibility

The public import path remains `maxapi`, while the distribution package name is `maxapi-sdk`.
