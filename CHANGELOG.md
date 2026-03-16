# Changelog

## 0.12.2

- перевыпуск после фикса release workflow в `main`, чтобы новый тег использовал action-based GitHub release вместо `gh release create`.

## 0.12.1

- исправлен release workflow: `github-release` теперь делает checkout перед `gh release create`;
- подготовлен повторный релиз после неуспешной первой попытки Trusted Publishing для `0.12.0`.

## 0.12.0

- первый публичный релиз в PyPI под distribution name `maxapi-sdk` с import path `maxapi`;
- добавлены FSM primitives: `State`, `StatesGroup`, `FSMContext`, `MemoryStorage`, `StateFilter`;
- добавлен `FSMMiddleware` и поддержка `Dispatcher(storage=...)`;
- добавлен plugin API: `BasePlugin`, `include_plugin()`, `include_plugins()`;
- добавлен structured callback payload parsing через `CallbackPayloadSchema`;
- добавлены поля внедрения `callback_payload`, `callback_payload_text`, `callback_payload_dict`;
- обновлён `CallbackData` filter: поддержка `startswith` и `contains`;
- добавлен workflow `.github/workflows/publish.yml` для GitHub Releases и PyPI Trusted Publishing;
- добавлены тесты на fourth iteration features.

## 0.11.0

- добавлены middleware и инъекция зависимостей в handlers;
- добавлены composable filters и alias-методы `message_handler`, `callback_query_handler`, `run_polling`;
- добавлен `InlineKeyboardBuilder` для inline keyboard MAX;
- добавлены media helpers: `upload_attachment`, `upload_image`, `upload_video`, `upload_audio`, `upload_file_attachment`, `send_image`, `send_video`, `send_audio`, `send_file`;
- добавлен compat layer: `maxapi.compat.LegacyBot`, `LegacyDispatcher`, `Keyboard`;
- добавлены тесты на third iteration features.

## 0.10.0

- вынесены `PollingRunner` и `WebhookRunner`;
- усилен transport слой;
- добавлены typed endpoints и базовый dispatcher.
