from __future__ import annotations

from io import BytesIO
from pathlib import Path

from maxapi import AudioAttachment, Bot, FileAttachment, ImageAttachment, VoiceAttachment
from maxapi.builders import attachment_from_raw, normalize_attachment
from maxapi.client.default import DefaultConnectionProperties
from maxapi.types import Message, SendMessageResponse, UpdateType, UploadResponse


class MediaRecorderBot(Bot):
    def __init__(self) -> None:
        super().__init__(
            token="token",
            default_connection=DefaultConnectionProperties(request_retries=1),
        )
        self.calls: list[tuple[str, str, dict]] = []
        self.uploaded_buffers: list[tuple[str, bytes, str]] = []

    async def request(self, method, path, model=None, *, is_return_raw=False, **kwargs):
        del model, is_return_raw
        self.calls.append((method, path, kwargs))
        if path == "/uploads":
            upload_type = kwargs["params"]["type"]
            return UploadResponse(url=f"https://upload.example/{upload_type}", token="seed-token")
        if path == "/messages":
            return SendMessageResponse.model_validate(
                {
                    "message": {
                        "message_id": "m-sent",
                        "chat_id": kwargs.get("params", {}).get("chat_id"),
                        "body": kwargs.get("json", {}),
                    }
                }
            )
        return {"ok": True}

    async def upload_file_buffer(self, *, filename: str, url: str, buffer: bytes, upload_type: str):
        self.uploaded_buffers.append((filename, buffer, upload_type))
        return {"url": f"cdn://{upload_type}/{filename}"}


async def test_send_voice_uses_audio_upload_flow_with_bytes():
    bot = MediaRecorderBot()

    await bot.send_voice(
        chat_id=501,
        filename="voice.ogg",
        buffer=b"voice-bytes",
        text="voice note",
    )

    upload_call = bot.calls[0]
    message_call = bot.calls[-1]

    assert upload_call[1] == "/uploads"
    assert upload_call[2]["params"]["type"] == "audio"
    assert bot.uploaded_buffers == [("voice.ogg", b"voice-bytes", "audio")]
    assert message_call[1] == "/messages"
    assert message_call[2]["json"]["attachments"][0]["type"] == "audio"
    assert message_call[2]["json"]["attachments"][0]["payload"]["token"] == "seed-token"


async def test_upload_attachment_supports_stream_source():
    bot = MediaRecorderBot()
    stream = BytesIO(b"image-bytes")

    attachment = await bot.upload_image(filename="banner.png", stream=stream)

    assert attachment["type"] == "image"
    assert attachment["payload"]["token"] == "seed-token"
    assert bot.uploaded_buffers == [("banner.png", b"image-bytes", "image")]


def test_message_exposes_typed_media_views():
    message = Message.model_validate(
        {
            "message_id": "m1",
            "chat_id": 42,
            "body": {
                "text": "media",
                "attachments": [
                    {"type": "image", "payload": {"token": "img-token", "url": "https://cdn/img"}},
                    {"type": "audio", "payload": {"token": "aud-token"}},
                    {"type": "file", "payload": {"token": "file-token"}},
                ],
            },
        }
    )

    assert isinstance(message.images[0], ImageAttachment)
    assert message.images[0].token == "img-token"
    assert isinstance(message.audios[0], AudioAttachment)
    assert isinstance(message.voices[0], AudioAttachment)
    assert isinstance(message.files[0], FileAttachment)
    assert len(message.typed_attachments) == 3


def test_typed_attachment_helpers_roundtrip():
    voice = VoiceAttachment(payload={"token": "voice-token"})
    normalized = normalize_attachment(voice)
    parsed = attachment_from_raw(normalized)

    assert normalized == {"type": "audio", "payload": {"token": "voice-token"}}
    assert isinstance(parsed, AudioAttachment)
    assert parsed.token == "voice-token"


async def test_send_image_accepts_path_or_bytes(tmp_path):
    bot = MediaRecorderBot()
    image_path = tmp_path / "photo.png"
    image_path.write_bytes(b"png-data")

    await bot.send_image(image_path, chat_id=123, text="path")
    await bot.send_image(chat_id=124, filename="photo.png", buffer=b"png-data-2", text="buffer")

    message_calls = [item for item in bot.calls if item[1] == "/messages"]
    assert len(message_calls) == 2
    assert message_calls[0][2]["params"]["chat_id"] == 123
    assert message_calls[1][2]["params"]["chat_id"] == 124
