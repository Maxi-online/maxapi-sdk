# Migration guide: 0.12.x → 0.13.0

## What changed

Version `0.13.0` expands the SDK media layer and standardizes package metadata for the `maxapi-sdk` distribution.

## Distribution name

- PyPI package: `maxapi-sdk`
- Python import path: `maxapi`

Installation example:

```bash
pip install maxapi-sdk
```

## New media capabilities

The SDK now provides first-class helpers for:

- `send_image()`
- `send_audio()`
- `send_voice()`
- `send_video()`
- `send_file()`
- `upload_voice()`
- bytes-based uploads
- stream-based uploads

## Before

```python
attachment = await bot.upload_audio("./voice.ogg")
await bot.send_message(chat_id=1001, text="Voice", attachments=[attachment])
```

## After

```python
await bot.send_voice("./voice.ogg", chat_id=1001, text="Voice")
```

## Bytes upload

```python
await bot.send_file(
    chat_id=1001,
    filename="report.pdf",
    buffer=pdf_bytes,
    text="Report",
)
```

## Stream upload

```python
with open("./audio.ogg", "rb") as file_object:
    await bot.send_voice(
        chat_id=1001,
        filename="audio.ogg",
        stream=file_object,
        text="Voice message",
    )
```

## Typed inbound media access

Incoming attachments are now available through typed accessors:

```python
@dispatcher.message_created()
async def handle_media(message):
    if message.images:
        print(message.images[0].token)
    if message.files:
        print(message.files[0].url)
```

Available accessors:

- `message.typed_attachments`
- `message.images`
- `message.audios`
- `message.voices`
- `message.videos`
- `message.files`

## Voice note

At the MAX Bot API level, voice delivery uses the audio upload flow. In `maxapi-sdk`, `send_voice()` and `upload_voice()` provide the public developer-facing interface for that workflow.
