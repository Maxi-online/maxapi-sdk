from __future__ import annotations

import json
from typing import Any, ClassVar, TypeVar, get_origin
from urllib.parse import quote, unquote

from pydantic import TypeAdapter

from .types import ApiModel

PayloadSchemaType = TypeVar("PayloadSchemaType", bound="CallbackPayloadSchema")


class CallbackPayloadError(ValueError):
    """Ошибка сериализации или десериализации callback payload."""


class CallbackPayloadSchema(ApiModel):
    """Структурированная схема callback payload.

    Пример:

        class AdminAction(CallbackPayloadSchema):
            prefix = "admin"
            action: str
            user_id: int

        payload = AdminAction(action="ban", user_id=42).pack()
        parsed = AdminAction.unpack(payload)
    """

    prefix: ClassVar[str] = ""
    sep: ClassVar[str] = ":"

    def pack(self) -> str:
        field_names = list(type(self).model_fields)
        values = [self.prefix or type(self).__name__.lower()]
        for field_name in field_names:
            values.append(_encode_component(getattr(self, field_name)))
        return self.sep.join(values)

    @classmethod
    def unpack(cls, payload: Any) -> PayloadSchemaType:
        payload_text = extract_callback_value(payload)
        if payload_text is None:
            raise CallbackPayloadError("Не удалось извлечь текстовый callback payload.")
        parts = payload_text.split(cls.sep)
        expected_prefix = cls.prefix or cls.__name__.lower()
        if not parts or parts[0] != expected_prefix:
            raise CallbackPayloadError(
                f"Некорректный prefix callback payload: ожидался {expected_prefix!r}."
            )
        field_names = list(cls.model_fields)
        raw_values = parts[1:]
        if len(raw_values) != len(field_names):
            raise CallbackPayloadError(
                "Количество значений callback payload не совпадает с количеством полей схемы."
            )
        converted: dict[str, Any] = {}
        for index, field_name in enumerate(field_names):
            field_info = cls.model_fields[field_name]
            converted[field_name] = _convert_component(
                unquote(raw_values[index]),
                field_info.annotation,
            )
        return cls(**converted)

    @classmethod
    def filter(cls, **conditions: Any):
        return CallbackSchemaFilter(cls, **conditions)


class CallbackSchemaFilter:
    def __init__(self, schema: type[CallbackPayloadSchema], **conditions: Any) -> None:
        self.schema = schema
        self.conditions = conditions

    async def __call__(self, event: Any) -> bool:
        update = getattr(event, "update", None)
        callback = getattr(update, "callback", None)
        payload = getattr(callback, "payload", None)
        try:
            parsed = self.schema.unpack(payload)
        except CallbackPayloadError:
            return False
        for key, expected_value in self.conditions.items():
            if getattr(parsed, key, None) != expected_value:
                return False
        return True


def extract_callback_value(payload: Any) -> str | None:
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "payload", "value"):
            item = payload.get(key)
            if isinstance(item, str):
                return item
        return None
    return None


def extract_callback_mapping(payload: Any) -> dict[str, Any] | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def _encode_component(value: Any) -> str:
    if isinstance(value, (dict, list)):
        serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    else:
        serialized = str(value)
    return quote(serialized, safe="")


def _convert_component(raw_value: str, annotation: Any) -> Any:
    origin = get_origin(annotation)
    candidate: Any = raw_value
    if annotation is Any:
        return raw_value
    if annotation in {dict, list} or origin in {dict, list, tuple, set}:
        try:
            candidate = json.loads(raw_value)
        except json.JSONDecodeError:
            candidate = raw_value
    adapter = TypeAdapter(annotation)
    return adapter.validate_python(candidate)
