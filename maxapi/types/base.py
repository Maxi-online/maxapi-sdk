from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    """Базовая модель SDK."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)
