from __future__ import annotations

from typing import Any


class State:
    """Описание состояния FSM."""

    def __init__(self) -> None:
        self.state: str | None = None

    def __set_name__(self, owner: type[StatesGroup], name: str) -> None:
        self.state = f"{owner.__name__}:{name}"

    def __get__(self, instance: Any, owner: type[StatesGroup]) -> "State":
        return self

    def __str__(self) -> str:
        if self.state is None:
            raise RuntimeError("Состояние ещё не связано с классом StatesGroup.")
        return self.state


class StatesGroup:
    """Базовый контейнер состояний."""

    @classmethod
    def states(cls) -> list[State]:
        values: list[State] = []
        for item in cls.__dict__.values():
            if isinstance(item, State):
                values.append(item)
        return values
