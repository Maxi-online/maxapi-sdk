from __future__ import annotations

from typing import Any, Iterable

SPECIAL_ROW_LIMIT_TYPES = {
    "link",
    "open_app",
    "request_contact",
    "request_geo_location",
}


class InlineKeyboardBuilder:
    """Builder для MAX inline keyboard."""

    def __init__(self) -> None:
        self._rows: list[list[dict[str, Any]]] = []
        self._pending: list[dict[str, Any]] = []

    def add(self, *buttons: dict[str, Any]) -> "InlineKeyboardBuilder":
        for button in buttons:
            self._pending.append(_normalize_button(button))
        return self

    def button(self, *, button_type: str, text: str, **extra: Any) -> "InlineKeyboardBuilder":
        button = {"type": button_type, "text": text}
        button.update({key: value for key, value in extra.items() if value is not None})
        return self.add(button)

    def callback(self, text: str, payload: str | dict[str, Any]) -> "InlineKeyboardBuilder":
        return self.button(button_type="callback", text=text, payload=payload)

    def link(self, text: str, url: str) -> "InlineKeyboardBuilder":
        return self.button(button_type="link", text=text, url=url)

    def request_contact(self, text: str) -> "InlineKeyboardBuilder":
        return self.button(button_type="request_contact", text=text)

    def request_geo_location(self, text: str) -> "InlineKeyboardBuilder":
        return self.button(button_type="request_geo_location", text=text)

    def open_app(
        self,
        text: str,
        *,
        url: str | None = None,
        app_id: str | None = None,
        payload: str | dict[str, Any] | None = None,
    ) -> "InlineKeyboardBuilder":
        return self.button(
            button_type="open_app",
            text=text,
            url=url,
            app_id=app_id,
            payload=payload,
        )

    def message(self, text: str, message_text: str) -> "InlineKeyboardBuilder":
        return self.button(button_type="message", text=text, message_text=message_text)

    def row(self, *buttons: dict[str, Any]) -> "InlineKeyboardBuilder":
        normalized = [_normalize_button(button) for button in buttons]
        if normalized:
            self._append_row(normalized)
        elif self._pending:
            self._append_row(self._consume_pending())
        return self

    def adjust(self, *sizes: int, repeat: bool = False) -> "InlineKeyboardBuilder":
        if not self._pending:
            return self
        if not sizes:
            sizes = (7,)
        index = 0
        pattern_index = 0
        while index < len(self._pending):
            row_size = sizes[pattern_index]
            row = self._pending[index:index + row_size]
            self._append_row(row)
            index += row_size
            if repeat:
                pattern_index = (pattern_index + 1) % len(sizes)
            else:
                pattern_index = min(pattern_index + 1, len(sizes) - 1)
        self._pending.clear()
        return self

    def as_markup(self) -> dict[str, Any]:
        self._flush_pending()
        return {"type": "inline_keyboard", "payload": {"buttons": self._rows}}

    def as_attachment(self) -> dict[str, Any]:
        return self.as_markup()

    def export(self) -> list[list[dict[str, Any]]]:
        self._flush_pending()
        return [[dict(button) for button in row] for row in self._rows]

    def _consume_pending(self) -> list[dict[str, Any]]:
        items = list(self._pending)
        self._pending.clear()
        return items

    def _flush_pending(self) -> None:
        if not self._pending:
            return
        self.adjust(7, repeat=True)

    def _append_row(self, row: Iterable[dict[str, Any]]) -> None:
        normalized = [dict(item) for item in row]
        if not normalized:
            return
        if len(normalized) > 7:
            raise ValueError("В одном ряду MAX inline keyboard может быть не более 7 кнопок.")
        if any(item.get("type") in SPECIAL_ROW_LIMIT_TYPES for item in normalized) and len(normalized) > 3:
            raise ValueError(
                "Ряд с кнопками link/open_app/request_contact/request_geo_location "
                "может содержать не более 3 кнопок."
            )
        if len(self._rows) >= 30:
            raise ValueError("MAX inline keyboard поддерживает не более 30 рядов.")
        total_buttons = sum(len(existing_row) for existing_row in self._rows) + len(normalized)
        if total_buttons > 210:
            raise ValueError("MAX inline keyboard поддерживает не более 210 кнопок.")
        self._rows.append(normalized)


def _normalize_button(button: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(button, dict):
        raise TypeError(f"Кнопка должна быть dict, получено: {button!r}")
    if "type" not in button or "text" not in button:
        raise ValueError("Кнопка должна содержать поля 'type' и 'text'.")
    return {key: value for key, value in button.items() if value is not None}
