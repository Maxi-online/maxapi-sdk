from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Iterable


@dataclass(slots=True)
class BaseAttachment:
    """Типизированное вложение MAX."""

    payload: dict[str, Any] = field(default_factory=dict)
    attachment_type: ClassVar[str] = ""

    def as_attachment(self) -> dict[str, Any]:
        return {"type": self.attachment_type, "payload": dict(self.payload)}

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None = None) -> "BaseAttachment":
        return cls(payload=dict(payload or {}))

    @property
    def token(self) -> str | None:
        value = self.payload.get("token")
        return value if isinstance(value, str) else None

    @property
    def url(self) -> str | None:
        value = self.payload.get("url")
        return value if isinstance(value, str) else None


@dataclass(slots=True)
class ImageAttachment(BaseAttachment):
    attachment_type: ClassVar[str] = "image"


@dataclass(slots=True)
class VideoAttachment(BaseAttachment):
    attachment_type: ClassVar[str] = "video"


@dataclass(slots=True)
class AudioAttachment(BaseAttachment):
    attachment_type: ClassVar[str] = "audio"


@dataclass(slots=True)
class VoiceAttachment(AudioAttachment):
    """SDK-обёртка для голосовых сообщений.

    На уровне MAX Bot API голосовые сообщения отправляются через audio-flow,
    поэтому наружу это voice-API, а в wire-format остаётся attachment типа audio.
    """

    attachment_type: ClassVar[str] = "audio"


@dataclass(slots=True)
class FileAttachment(BaseAttachment):
    attachment_type: ClassVar[str] = "file"


_ATTACHMENT_CLASS_MAP: dict[str, type[BaseAttachment]] = {
    "image": ImageAttachment,
    "video": VideoAttachment,
    "audio": AudioAttachment,
    "file": FileAttachment,
}


def make_attachment(attachment_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {"type": attachment_type, "payload": payload}


def image_attachment(
    *,
    token: str | None = None,
    url: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = _build_payload(token=token, url=url, extra=extra)
    return make_attachment("image", payload)


def video_attachment(
    *,
    token: str | None = None,
    url: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = _build_payload(token=token, url=url, extra=extra)
    return make_attachment("video", payload)


def audio_attachment(
    *,
    token: str | None = None,
    url: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = _build_payload(token=token, url=url, extra=extra)
    return make_attachment("audio", payload)


def voice_attachment(
    *,
    token: str | None = None,
    url: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = _build_payload(token=token, url=url, extra=extra)
    return make_attachment("audio", payload)


def file_attachment(
    *,
    token: str | None = None,
    url: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = _build_payload(token=token, url=url, extra=extra)
    return make_attachment("file", payload)


def attachment_from_raw(item: Any) -> BaseAttachment | dict[str, Any]:
    normalized = normalize_attachment(item)
    attachment_type = normalized.get("type")
    payload = normalized.get("payload")
    if not isinstance(payload, dict):
        return normalized
    attachment_class = _ATTACHMENT_CLASS_MAP.get(attachment_type)
    if attachment_class is None:
        return normalized
    return attachment_class.from_payload(payload)


def extract_typed_attachments(
    attachments: Iterable[Any] | None,
    *,
    attachment_type: str | None = None,
) -> list[BaseAttachment]:
    typed: list[BaseAttachment] = []
    for item in attachments or []:
        parsed = attachment_from_raw(item)
        if not isinstance(parsed, BaseAttachment):
            continue
        if attachment_type is None or parsed.attachment_type == attachment_type:
            typed.append(parsed)
    return typed


def normalize_attachment(item: Any) -> dict[str, Any]:
    if item is None:
        raise TypeError("Attachment не может быть None.")
    if isinstance(item, BaseAttachment):
        return item.as_attachment()
    if isinstance(item, dict):
        return item
    if hasattr(item, "as_attachment"):
        return item.as_attachment()
    if hasattr(item, "model_dump"):
        return item.model_dump(by_alias=True, exclude_none=True)
    raise TypeError(f"Неподдерживаемый attachment: {item!r}")


def normalize_attachments(
    attachments: Iterable[Any] | None = None,
    *,
    keyboard: Any | None = None,
) -> list[dict[str, Any]] | None:
    normalized: list[dict[str, Any]] = []
    if attachments is not None:
        for item in attachments:
            normalized.append(normalize_attachment(item))
    if keyboard is not None:
        normalized.append(normalize_attachment(keyboard))
    if not normalized:
        return None
    return normalized


def build_uploaded_attachment(
    *,
    upload_type: str,
    upload_response_token: str | None,
    uploaded_payload: dict[str, Any],
) -> dict[str, Any]:
    payload = dict(uploaded_payload)
    if payload.get("token") is None and upload_response_token is not None:
        payload["token"] = upload_response_token
    return make_attachment(upload_type, payload)


def _build_payload(
    *,
    token: str | None,
    url: str | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    payload = dict(extra)
    if token is not None:
        payload["token"] = token
    if url is not None:
        payload["url"] = url
    return payload
