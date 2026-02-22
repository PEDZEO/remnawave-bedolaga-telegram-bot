from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.database.models import MainMenuButtonActionType, MainMenuButtonVisibility


def _clean_text(value: str) -> str:
    cleaned = (value or '').strip()
    if not cleaned:
        raise ValueError('Text cannot be empty')
    return cleaned


def _validate_action_value(value: str) -> str:
    cleaned = (value or '').strip()
    if not cleaned:
        raise ValueError('Action value cannot be empty')
    if not cleaned.lower().startswith(('http://', 'https://')):
        raise ValueError('Action value must start with http:// or https://')
    return cleaned


class MainMenuButtonResponse(BaseModel):
    id: int
    text: str
    action_type: MainMenuButtonActionType
    action_value: str
    visibility: MainMenuButtonVisibility
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class MainMenuButtonCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=64)
    action_type: MainMenuButtonActionType
    action_value: str = Field(..., min_length=1, max_length=1024)
    visibility: MainMenuButtonVisibility = MainMenuButtonVisibility.ALL
    is_active: bool = True
    display_order: int | None = Field(None, ge=0)

    @field_validator('text')
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _clean_text(value)

    @field_validator('action_value')
    @classmethod
    def validate_action_value(cls, value: str) -> str:
        return _validate_action_value(value)


class MainMenuButtonUpdateRequest(BaseModel):
    text: str | None = Field(None, min_length=1, max_length=64)
    action_type: MainMenuButtonActionType | None = None
    action_value: str | None = Field(None, min_length=1, max_length=1024)
    visibility: MainMenuButtonVisibility | None = None
    is_active: bool | None = None
    display_order: int | None = Field(None, ge=0)

    @field_validator('text')
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _clean_text(value)

    @field_validator('action_value')
    @classmethod
    def validate_action_value(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_action_value(value)


class MainMenuButtonListResponse(BaseModel):
    items: list[MainMenuButtonResponse]
    total: int
    limit: int
    offset: int
