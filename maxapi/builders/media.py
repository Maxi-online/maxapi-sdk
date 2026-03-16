from __future__ import annotations

from typing import Any, Iterable


def make_attachment(attachment_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {"type": attachment_type, "payload": payload}


def image_attachment(*, token: str | None = None, url: str | None = None, **extra: Any) -> dict[str, Any]:
    payload = _build_payload(token=token, url=url, extra=extra)
    return make_attachment("image", payload)


def video_attachment(*, token: str | None = None, url: str | None = None, **extra: Any) -> dict[str, Any]:
    payload = _build_payload(token=token, url=url, extra=extra)
    return make_attachment("video", payload)


def audio_attachment(*, token: str | None = None, url: str | None = None, **extra: Any) -> dict[str, Any]:
    payload = _build_payload(token=token, url=url, extra=extra)
    return make_attachment("audio", payload)


def file_attachment(*, token: str | None = None, url: str | None = None, **extra: Any) -> dict[str, Any]:
    payload = _build_payload(token=token, url=url, extra=extra)
    return make_attachment("file", payload)


def normalize_attachment(item: Any) -> dict[str, Any]:
    if item is None:
        raise TypeError("Attachment не может быть None.")
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
