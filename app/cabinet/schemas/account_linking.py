"""Schemas for account linking flow."""

from pydantic import BaseModel, Field


class LinkedIdentity(BaseModel):
    provider: str = Field(..., description='Identity provider name')
    provider_user_id_masked: str = Field(..., description='Masked provider user id')


class LinkedIdentitiesResponse(BaseModel):
    identities: list[LinkedIdentity]


class LinkCodeCreateResponse(BaseModel):
    code: str = Field(..., description='One-time account link code')
    expires_in_seconds: int = Field(..., description='Code TTL in seconds')


class LinkCodePreviewRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=32, description='One-time account link code')


class LinkCodePreviewResponse(BaseModel):
    source_user_id: int = Field(..., description='Source account user id')
    source_identity_hints: dict[str, str] = Field(..., description='Masked identities of source account')


class LinkCodeConfirmRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=32, description='One-time account link code')


class LinkCodeConfirmResponse(BaseModel):
    message: str = Field(..., description='Confirmation message')
    source_user_id: int = Field(..., description='Target source account id after linking')
