# Changelog

## 0.13.0

- added first-class media workflows for images, audio, voice, video, and files;
- added bytes and stream upload support alongside file-path uploads;
- added typed attachment helpers: `ImageAttachment`, `AudioAttachment`, `VoiceAttachment`, `VideoAttachment`, `FileAttachment`;
- added typed inbound media accessors on messages: `images`, `audios`, `voices`, `videos`, `files`, `typed_attachments`;
- added `send_voice()` and `upload_voice()` as public SDK methods backed by the MAX audio upload flow;
- updated package metadata for the `maxapi-sdk` distribution name;
- refreshed README and package presentation in a more concise and professional format;
- added tests for media workflows and typed attachment parsing.

## 0.12.0

- added FSM primitives: `State`, `StatesGroup`, `FSMContext`, `MemoryStorage`, `StateFilter`;
- added `FSMMiddleware` and `Dispatcher(storage=...)` support;
- added plugin API: `BasePlugin`, `include_plugin()`, `include_plugins()`;
- added structured callback payload parsing via `CallbackPayloadSchema`;
- added injected values `callback_payload`, `callback_payload_text`, `callback_payload_dict`;
- updated `CallbackData` filter with `startswith` and `contains` support;
- added `.github/workflows/publish.yml` for GitHub Releases and PyPI Trusted Publishing;
- added tests for fourth-iteration features.

## 0.11.0

- added middleware and handler dependency injection;
- added composable filters and alias methods `message_handler`, `callback_query_handler`, `run_polling`;
- added `InlineKeyboardBuilder` for MAX inline keyboard;
- added media helpers: `upload_attachment`, `upload_image`, `upload_video`, `upload_audio`, `upload_file_attachment`, `send_image`, `send_video`, `send_audio`, `send_file`;
- added compatibility layer: `maxapi.compat.LegacyBot`, `LegacyDispatcher`, `Keyboard`;
- added tests for third-iteration features.

## 0.10.0

- extracted `PollingRunner` and `WebhookRunner`;
- strengthened transport layer;
- added typed endpoints and a base dispatcher.
