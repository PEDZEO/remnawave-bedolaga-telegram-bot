"""Schemas for account linking flow."""

from datetime import datetime

from pydantic import BaseModel, Field

from .auth import AuthResponse


class LinkedIdentity(BaseModel):
    provider: str = Field(..., description='Identity provider name')
    provider_user_id_masked: str = Field(..., description='Masked provider user id')
    can_unlink: bool = Field(True, description='Whether identity can be unlinked')
    blocked_reason: str | None = Field(None, description='Reason code why unlink is blocked')
    blocked_until: datetime | None = Field(
        None,
        description='ISO datetime when unlink block ends (for cooldown-based restrictions)',
    )
    retry_after_seconds: int | None = Field(
        None,
        description='Seconds remaining until action is available again',
    )


class TelegramRelinkStatus(BaseModel):
    can_start_relink: bool = Field(
        ...,
        description='Whether user can start Telegram relink right now',
    )
    requires_unlink_first: bool = Field(
        ...,
        description='Whether current Telegram must be unlinked before linking another one',
    )
    cooldown_until: datetime | None = Field(
        None,
        description='ISO datetime when Telegram relink cooldown ends',
    )
    retry_after_seconds: int | None = Field(
        None,
        description='Seconds remaining until Telegram relink is available',
    )


class LinkedIdentitiesResponse(BaseModel):
    identities: list[LinkedIdentity]
    telegram_relink: TelegramRelinkStatus


class LinkProviderAuthorizeResponse(BaseModel):
    provider: str = Field(..., description='Identity provider name')
    authorize_url: str = Field(..., description='OAuth authorize URL')
    state: str = Field(..., description='OAuth state token')


class LinkProviderCallbackRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=2048, description='Authorization code from provider')
    state: str = Field(..., min_length=1, max_length=128, description='State token from provider callback')
    device_id: str | None = Field(None, max_length=256, description='Optional VK device id')
    type: str | None = Field(None, max_length=64, description='Optional provider callback type')


class LinkOperationResponse(BaseModel):
    status: str = Field(..., description='Operation status: success, manual, or error')
    provider: str = Field(..., description='Identity provider name')
    message: str = Field(..., description='User-facing status message')
    code: str | None = Field(None, description='Machine-readable status/error code')
    switched_account: bool = Field(
        False,
        description='Whether primary account changed and client should switch auth session',
    )


class PendingLinkResultResponse(BaseModel):
    pending: bool = Field(..., description='Whether there is a pending external link result')
    status: str | None = Field(None, description='Operation status: success, manual, or error')
    provider: str | None = Field(None, description='Identity provider name')
    message: str | None = Field(None, description='User-facing status message')
    code: str | None = Field(None, description='Machine-readable status/error code')
    auth_response: AuthResponse | None = Field(
        None,
        description='Fresh auth payload when primary account changed during external link',
    )


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


class UnlinkIdentityRequestResponse(BaseModel):
    provider: str
    request_token: str
    expires_in_seconds: int


class UnlinkIdentityConfirmRequest(BaseModel):
    request_token: str = Field(..., min_length=16, max_length=256)
    otp_code: str = Field(..., min_length=6, max_length=6, description='6-digit OTP sent via Telegram')


class UnlinkIdentityResponse(BaseModel):
    message: str
    provider: str


class ManualMergeRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=32, description='One-time account link code')
    comment: str | None = Field(
        None,
        min_length=0,
        max_length=1000,
        description='Optional user comment for admin manual merge review',
    )


class ManualMergeResponse(BaseModel):
    message: str = Field(..., description='Manual merge request status')
    ticket_id: int = Field(..., description='Created support ticket id')


class ManualMergeTicketStatusResponse(BaseModel):
    ticket_id: int = Field(..., description='Support ticket id')
    status: str = Field(..., description='Ticket status')
    decision: str | None = Field(None, description='Merge decision: approve/reject')
    created_at: datetime = Field(..., description='Ticket creation datetime')
    updated_at: datetime = Field(..., description='Ticket last update datetime')
    source_user_id: int | None = Field(None, description='Source user from code (if parsed)')
    current_user_id: int | None = Field(None, description='Request owner user id (if parsed)')
    resolution_comment: str | None = Field(None, description='Admin resolution comment')


class AdminManualMergeItem(BaseModel):
    ticket_id: int
    status: str
    decision: str | None = None
    created_at: datetime
    updated_at: datetime
    requester_user_id: int
    source_user_id: int | None = None
    current_user_id: int | None = None
    requester_identity_hints: dict[str, str] = Field(default_factory=dict)
    source_identity_hints: dict[str, str] = Field(default_factory=dict)
    user_comment: str | None = None
    resolution_comment: str | None = None


class AdminManualMergeListResponse(BaseModel):
    items: list[AdminManualMergeItem]
    total: int
    page: int
    per_page: int
    pages: int


class AdminManualMergeResolveRequest(BaseModel):
    action: str = Field(..., description='approve or reject')
    primary_user_id: int | None = Field(None, description='Primary account id for approved merge')
    comment: str | None = Field(None, min_length=0, max_length=1000)
