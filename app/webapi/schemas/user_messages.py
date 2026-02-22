from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _normalize_text(value: str) -> str:
    cleaned = (value or '').strip()
    if not cleaned:
        raise ValueError('Message text cannot be empty')
    return cleaned


class UserMessageResponse(BaseModel):
    id: int
    message_text: str
    is_active: bool
    sort_order: int
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class UserMessageCreateRequest(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=4000)
    is_active: bool = True
    sort_order: int = Field(0, ge=0)

    @field_validator('message_text')
    @classmethod
    def validate_message_text(cls, value: str) -> str:
        return _normalize_text(value)


class UserMessageUpdateRequest(BaseModel):
    message_text: str | None = Field(None, min_length=1, max_length=4000)
    is_active: bool | None = None
    sort_order: int | None = Field(None, ge=0)

    @field_validator('message_text')
    @classmethod
    def validate_message_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _normalize_text(value)


class UserMessageListResponse(BaseModel):
    items: list[UserMessageResponse]
    total: int
    limit: int
    offset: int
