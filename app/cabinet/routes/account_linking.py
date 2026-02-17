"""Account linking routes for cabinet authentication."""

import hashlib
import secrets
from datetime import UTC, datetime

import structlog
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.crud.user import get_user_by_id
from app.database.models import CabinetRefreshToken, Ticket, TicketMessage, User, UserStatus
from app.handlers.tickets import notify_admins_about_new_ticket
from app.utils.cache import cache, cache_key

from ..dependencies import get_cabinet_db, get_current_cabinet_user
from ..schemas.account_linking import (
    UnlinkIdentityConfirmRequest,
    UnlinkIdentityRequestResponse,
    UnlinkIdentityResponse,
    ManualMergeTicketStatusResponse,
    LinkCodeConfirmRequest,
    LinkCodeCreateResponse,
    LinkCodePreviewRequest,
    LinkCodePreviewResponse,
    LinkedIdentitiesResponse,
    LinkedIdentity,
    ManualMergeRequest,
    ManualMergeResponse,
)
from ..schemas.auth import AuthResponse
from ..services.account_linking import (
    LINK_CODE_TTL_SECONDS,
    LinkCodeAttemptsExceededError,
    LinkCodeConflictError,
    LinkCodeInvalidError,
    confirm_link_code,
    create_link_code,
    get_user_identity_hints,
    preview_link_code,
)
from ..services.manual_merge_ticket import (
    MANUAL_MERGE_TICKET_TITLE,
    build_manual_merge_ticket_message,
    parse_manual_merge_payload,
    parse_manual_merge_resolution,
)
from .auth import _create_auth_response, _store_refresh_token


logger = structlog.get_logger(__name__)
router = APIRouter(prefix='/auth', tags=['Cabinet Account Linking'])

UNLINK_CONFIRM_TTL_SECONDS = 10 * 60
UNLINK_COOLDOWN_SECONDS = 24 * 60 * 60
TELEGRAM_RELINK_COOLDOWN_SECONDS = 30 * 24 * 60 * 60
UNLINK_OTP_LENGTH = 6
UNLINK_OTP_MAX_ATTEMPTS = 5
UNLINK_OTP_SEND_COOLDOWN_SECONDS = 60
UNLINK_OTP_SEND_WINDOW_SECONDS = 60 * 60
UNLINK_OTP_SEND_MAX_PER_WINDOW = 5

_UNLINK_PROVIDER_ATTRS: dict[str, str] = {
    'telegram': 'telegram_id',
    'google': 'google_id',
    'yandex': 'yandex_id',
    'discord': 'discord_id',
    'vk': 'vk_id',
}


def _unlink_request_key(token: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'request', token)


def _unlink_cooldown_key(user_id: int, provider: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'cooldown', user_id, provider)


def _unlink_otp_attempts_key(token: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'otp_attempts', token)


def _unlink_otp_send_cooldown_key(user_id: int, provider: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'otp_send_cooldown', user_id, provider)


def _unlink_otp_send_counter_key(user_id: int, provider: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'otp_send_counter', user_id, provider)


def _unlink_otp_send_block_key(user_id: int, provider: str) -> str:
    return cache_key('cabinet', 'unlink_identity', 'otp_send_block', user_id, provider)


def _telegram_relink_cooldown_key(user_id: int) -> str:
    return cache_key('cabinet', 'telegram_relink', 'cooldown', user_id)


def _telegram_unlink_marker_key(user_id: int) -> str:
    return cache_key('cabinet', 'telegram_relink', 'unlink_marker', user_id)


def _unlink_otp_hash(otp_code: str) -> str:
    pepper = settings.get_cabinet_jwt_secret()
    return hashlib.sha256(f'{pepper}:unlink_otp:{otp_code}'.encode()).hexdigest()


def _generate_otp_code() -> str:
    # cryptographically secure 6-digit OTP
    value = secrets.randbelow(10**UNLINK_OTP_LENGTH)
    return f'{value:0{UNLINK_OTP_LENGTH}d}'


_cached_bot: Bot | None = None


def _get_bot() -> Bot:
    global _cached_bot
    if _cached_bot is None:
        _cached_bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return _cached_bot


async def _send_unlink_otp_to_telegram(telegram_id: int, provider: str, otp_code: str) -> None:
    bot = _get_bot()
    text = (
        '🔐 <b>Подтверждение отвязки входа</b>\n\n'
        f'Провайдер: <b>{provider}</b>\n'
        f'Код подтверждения: <code>{otp_code}</code>\n\n'
        f'Код действует {UNLINK_CONFIRM_TTL_SECONDS // 60} минут.\n'
        'Если это были не вы, ничего не подтверждайте.'
    )
    await bot.send_message(chat_id=telegram_id, text=text)


async def _get_unlink_block_reason(user: User, provider: str) -> str | None:
    attr_name = _UNLINK_PROVIDER_ATTRS.get(provider)
    if not attr_name:
        return 'provider_not_supported'

    linked_value = getattr(user, attr_name, None)
    if linked_value is None:
        return 'identity_not_linked'

    linked_count = len(get_user_identity_hints(user))
    if linked_count <= 1:
        return 'last_identity'

    if user.auth_type == provider:
        return 'current_auth_provider'

    if user.telegram_id is None:
        return 'telegram_required'

    cooldown_payload = await cache.get(_unlink_cooldown_key(user.id, provider))
    if isinstance(cooldown_payload, dict) and cooldown_payload.get('active'):
        return 'cooldown_active'

    return None


def _link_error_to_http(exc: Exception) -> HTTPException:
    detail = {'code': getattr(exc, 'code', 'link_code_error'), 'message': str(exc)}
    code = detail['code']
    if code == 'link_code_attempts_exceeded':
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
    if code in {
        'link_code_invalid',
        'link_code_same_account',
        'link_code_storage_error',
        'link_code_attempts_error',
        'link_code_user_not_found',
    }:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if code in {
        'manual_merge_required',
        'link_code_identity_conflict',
        'link_code_source_inactive',
        'link_code_target_inactive',
    }:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


async def _ensure_telegram_relink_allowed(target_user: User, source_user: User) -> None:
    """Guard Telegram account replacement and enforce relink cooldown."""
    if source_user.telegram_id is None:
        return

    if target_user.telegram_id is not None and target_user.telegram_id != source_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': 'telegram_relink_requires_unlink',
                'message': 'To link another Telegram account, unlink current Telegram first',
            },
        )

    if target_user.telegram_id is None:
        cooldown_payload = await cache.get(_telegram_relink_cooldown_key(target_user.id))
        if isinstance(cooldown_payload, dict) and cooldown_payload.get('active'):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    'code': 'telegram_relink_cooldown_active',
                    'message': 'Telegram account can be changed only once per 30 days',
                    'retry_after_seconds': TELEGRAM_RELINK_COOLDOWN_SECONDS,
                },
            )


@router.get('/identities', response_model=LinkedIdentitiesResponse)
async def get_linked_identities(user: User = Depends(get_current_cabinet_user)):
    """Get linked login identities for current user."""
    hints = get_user_identity_hints(user)
    reasons = {provider: await _get_unlink_block_reason(user, provider) for provider in hints}
    identities = [
        LinkedIdentity(
            provider=provider,
            provider_user_id_masked=provider_user_id_masked,
            can_unlink=reasons.get(provider) is None,
            blocked_reason=reasons.get(provider),
        )
        for provider, provider_user_id_masked in sorted(hints.items())
    ]
    return LinkedIdentitiesResponse(identities=identities)


@router.post('/identities/{provider}/unlink/request', response_model=UnlinkIdentityRequestResponse)
async def request_unlink_identity(
    provider: str,
    user: User = Depends(get_current_cabinet_user),
):
    """Start unlink flow and return short-lived request token for confirmation."""
    normalized_provider = provider.strip().lower()
    reason = await _get_unlink_block_reason(user, normalized_provider)
    if reason:
        status_code = status.HTTP_409_CONFLICT if reason != 'provider_not_supported' else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail={'code': 'unlink_not_allowed', 'reason': reason, 'message': 'Unlink is not allowed for this identity'},
        )

    cooldown_payload = await cache.get(_unlink_otp_send_cooldown_key(user.id, normalized_provider))
    if isinstance(cooldown_payload, dict) and cooldown_payload.get('active'):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                'code': 'unlink_otp_resend_cooldown',
                'message': 'Please wait before requesting another OTP code',
                'retry_after_seconds': UNLINK_OTP_SEND_COOLDOWN_SECONDS,
            },
        )

    blocked_payload = await cache.get(_unlink_otp_send_block_key(user.id, normalized_provider))
    if isinstance(blocked_payload, dict) and blocked_payload.get('active'):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                'code': 'unlink_otp_rate_limited',
                'message': 'Too many OTP requests for this identity. Try again later.',
            },
        )

    send_count = await cache.increment(_unlink_otp_send_counter_key(user.id, normalized_provider), 1)
    if send_count is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'code': 'unlink_otp_counter_error', 'message': 'Failed to validate OTP request limit'},
        )
    if send_count == 1:
        await cache.expire(_unlink_otp_send_counter_key(user.id, normalized_provider), UNLINK_OTP_SEND_WINDOW_SECONDS)
    if send_count > UNLINK_OTP_SEND_MAX_PER_WINDOW:
        await cache.set(
            _unlink_otp_send_block_key(user.id, normalized_provider),
            {'active': True},
            expire=UNLINK_OTP_SEND_WINDOW_SECONDS,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                'code': 'unlink_otp_rate_limited',
                'message': 'Too many OTP requests for this identity. Try again later.',
            },
        )

    request_token = secrets.token_urlsafe(24)
    otp_code = _generate_otp_code()
    payload = {
        'user_id': user.id,
        'provider': normalized_provider,
        'requested_at': datetime.now(UTC).isoformat(),
        'otp_hash': _unlink_otp_hash(otp_code),
    }
    saved = await cache.set(_unlink_request_key(request_token), payload, expire=UNLINK_CONFIRM_TTL_SECONDS)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'code': 'unlink_request_storage_error', 'message': 'Failed to create unlink request'},
        )

    if user.telegram_id is None:
        await cache.delete(_unlink_request_key(request_token))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': 'unlink_not_allowed',
                'reason': 'telegram_required',
                'message': 'Telegram is required for unlink confirmation',
            },
        )

    try:
        await _send_unlink_otp_to_telegram(user.telegram_id, normalized_provider, otp_code)
    except Exception as exc:
        await cache.delete(_unlink_request_key(request_token))
        # Roll back counter effect when delivery fails.
        await cache.increment(_unlink_otp_send_counter_key(user.id, normalized_provider), -1)
        logger.warning(
            'Failed to send unlink OTP to telegram',
            user_id=user.id,
            provider=normalized_provider,
            error=exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={'code': 'unlink_otp_delivery_failed', 'message': 'Failed to send OTP to Telegram'},
        ) from exc

    await cache.set(
        _unlink_otp_send_cooldown_key(user.id, normalized_provider),
        {'active': True},
        expire=UNLINK_OTP_SEND_COOLDOWN_SECONDS,
    )

    return UnlinkIdentityRequestResponse(
        provider=normalized_provider,
        request_token=request_token,
        expires_in_seconds=UNLINK_CONFIRM_TTL_SECONDS,
    )


@router.post('/identities/{provider}/unlink/confirm', response_model=UnlinkIdentityResponse)
async def confirm_unlink_identity(
    provider: str,
    request: UnlinkIdentityConfirmRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Confirm identity unlink and revoke all refresh sessions for security."""
    normalized_provider = provider.strip().lower()
    payload = await cache.get(_unlink_request_key(request.request_token))
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'unlink_request_invalid', 'message': 'Unlink request is invalid or expired'},
        )

    if payload.get('user_id') != user.id or payload.get('provider') != normalized_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'unlink_request_mismatch', 'message': 'Unlink request does not match current user/provider'},
        )

    otp_hash = payload.get('otp_hash')
    if not isinstance(otp_hash, str) or not otp_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'unlink_request_invalid', 'message': 'Unlink request payload is invalid'},
        )

    attempts = await cache.increment(_unlink_otp_attempts_key(request.request_token), 1)
    if attempts is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'code': 'unlink_otp_attempts_error', 'message': 'Failed to validate OTP attempts'},
        )
    if attempts == 1:
        await cache.expire(_unlink_otp_attempts_key(request.request_token), UNLINK_CONFIRM_TTL_SECONDS)
    if attempts > UNLINK_OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={'code': 'unlink_otp_attempts_exceeded', 'message': 'Too many OTP attempts'},
        )

    if _unlink_otp_hash(request.otp_code.strip()) != otp_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'unlink_otp_invalid', 'message': 'OTP code is invalid'},
        )

    reason = await _get_unlink_block_reason(user, normalized_provider)
    if reason:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'code': 'unlink_not_allowed', 'reason': reason, 'message': 'Unlink is not allowed for this identity'},
        )

    attr_name = _UNLINK_PROVIDER_ATTRS[normalized_provider]
    setattr(user, attr_name, None)
    user.updated_at = datetime.now(UTC).replace(tzinfo=None)

    # Security: invalidate refresh sessions after identity change.
    await db.execute(
        update(CabinetRefreshToken)
        .where(
            CabinetRefreshToken.user_id == user.id,
            CabinetRefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC).replace(tzinfo=None))
    )

    await db.commit()

    await cache.delete(_unlink_request_key(request.request_token))
    await cache.delete(_unlink_otp_attempts_key(request.request_token))
    await cache.set(
        _unlink_cooldown_key(user.id, normalized_provider),
        {'active': True},
        expire=UNLINK_COOLDOWN_SECONDS,
    )
    if normalized_provider == 'telegram':
        await cache.set(
            _telegram_unlink_marker_key(user.id),
            {'active': True},
            expire=TELEGRAM_RELINK_COOLDOWN_SECONDS,
        )

    logger.info('Identity unlinked', user_id=user.id, provider=normalized_provider)
    return UnlinkIdentityResponse(message='Identity unlinked successfully', provider=normalized_provider)


@router.post('/link-code/create', response_model=LinkCodeCreateResponse)
async def create_account_link_code(user: User = Depends(get_current_cabinet_user)):
    """Create one-time code that can be used to link another account into current account."""
    if user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Only active accounts can create link codes',
        )
    code = await create_link_code(user)
    return LinkCodeCreateResponse(code=code, expires_in_seconds=LINK_CODE_TTL_SECONDS)


@router.post('/link-code/preview', response_model=LinkCodePreviewResponse)
async def preview_account_link_code(
    request: LinkCodePreviewRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Validate code and return source account hints before confirmation."""
    try:
        source_user_id = await preview_link_code(request.code, user.id)
    except LinkCodeAttemptsExceededError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeInvalidError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeConflictError as exc:
        raise _link_error_to_http(exc) from exc

    source_user = await get_user_by_id(db, source_user_id)
    if not source_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'link_code_user_not_found', 'message': 'Source account not found'},
        )
    if source_user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'code': 'link_code_source_inactive', 'message': 'Source account is not active'},
        )
    await _ensure_telegram_relink_allowed(user, source_user)

    return LinkCodePreviewResponse(
        source_user_id=source_user.id,
        source_identity_hints=get_user_identity_hints(source_user),
    )


@router.post('/link-code/confirm', response_model=AuthResponse)
async def confirm_account_link_code(
    request: LinkCodeConfirmRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Confirm linking: move identities to source account and return new auth session for source."""
    try:
        source_user_id = await preview_link_code(request.code, user.id)
    except LinkCodeAttemptsExceededError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeInvalidError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeConflictError as exc:
        raise _link_error_to_http(exc) from exc

    source_user_for_guard = await get_user_by_id(db, source_user_id)
    if not source_user_for_guard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'link_code_user_not_found', 'message': 'Source account not found'},
        )
    await _ensure_telegram_relink_allowed(user, source_user_for_guard)

    try:
        source_user = await confirm_link_code(db, request.code, user)
    except LinkCodeAttemptsExceededError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeInvalidError as exc:
        raise _link_error_to_http(exc) from exc
    except LinkCodeConflictError as exc:
        raise _link_error_to_http(exc) from exc

    source_user.cabinet_last_login = datetime.now(UTC).replace(tzinfo=None)
    await db.commit()
    auth_response = _create_auth_response(source_user)
    await _store_refresh_token(db, source_user.id, auth_response.refresh_token, device_info='account-linking')

    logger.info('Account linking auth session switched to source account', source_user_id=source_user.id)

    # If user had recently unlinked Telegram and then linked another one, start 30-day change cooldown.
    if source_user.id == user.id and source_user.telegram_id is not None:
        unlink_marker = await cache.get(_telegram_unlink_marker_key(user.id))
        if isinstance(unlink_marker, dict) and unlink_marker.get('active'):
            await cache.set(
                _telegram_relink_cooldown_key(user.id),
                {'active': True},
                expire=TELEGRAM_RELINK_COOLDOWN_SECONDS,
            )
            await cache.delete(_telegram_unlink_marker_key(user.id))

    return auth_response


@router.post('/link-code/manual-request', response_model=ManualMergeResponse)
async def request_manual_merge(
    request: ManualMergeRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Create manual merge support ticket for disputed account linking cases."""
    if not settings.is_support_tickets_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'code': 'support_disabled', 'message': 'Support tickets are disabled'},
        )

    try:
        source_user_id = await preview_link_code(request.code, user.id)
    except (LinkCodeAttemptsExceededError, LinkCodeInvalidError, LinkCodeConflictError) as exc:
        raise _link_error_to_http(exc) from exc

    source_user = await get_user_by_id(db, source_user_id)
    if not source_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'link_code_user_not_found', 'message': 'Source account not found'},
        )
    await _ensure_telegram_relink_allowed(user, source_user)

    message_text = build_manual_merge_ticket_message(
        current_user_id=user.id,
        source_user_id=source_user.id,
        current_user_hints=get_user_identity_hints(user),
        source_user_hints=get_user_identity_hints(source_user),
        comment=request.comment,
    )

    ticket = Ticket(
        user_id=user.id,
        title=MANUAL_MERGE_TICKET_TITLE,
        status='open',
        priority='high',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(ticket)
    await db.flush()

    initial_message = TicketMessage(
        ticket_id=ticket.id,
        user_id=user.id,
        message_text=message_text,
        is_from_admin=False,
        created_at=datetime.utcnow(),
    )
    db.add(initial_message)
    await db.commit()
    await db.refresh(ticket)

    try:
        await notify_admins_about_new_ticket(ticket, db)
    except Exception as exc:
        logger.warning('Failed to notify admins about manual merge ticket', ticket_id=ticket.id, error=exc)

    return ManualMergeResponse(
        message='Manual merge request has been sent to support',
        ticket_id=ticket.id,
    )


@router.get('/link-code/manual-request/latest', response_model=ManualMergeTicketStatusResponse | None)
async def get_latest_manual_merge_request(
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Return latest manual merge ticket status for current user."""
    stmt = (
        select(Ticket)
        .where(Ticket.user_id == user.id, Ticket.title == MANUAL_MERGE_TICKET_TITLE)
        .options(selectinload(Ticket.messages))
        .order_by(desc(Ticket.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()
    if ticket is None:
        return None

    source_user_id: int | None = None
    current_user_id: int | None = None
    decision: str | None = None
    resolution_comment: str | None = None

    for message in ticket.messages:
        if not message.message_text:
            continue
        payload = parse_manual_merge_payload(message.message_text)
        if payload:
            source_user_id = payload['source_user_id']
            current_user_id = payload['current_user_id']
        resolution = parse_manual_merge_resolution(message.message_text)
        if resolution:
            decision = str(resolution['action'])
            resolution_comment = str(resolution.get('comment')) if resolution.get('comment') else None

    return ManualMergeTicketStatusResponse(
        ticket_id=ticket.id,
        status=ticket.status,
        decision=decision,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at or ticket.created_at,
        source_user_id=source_user_id,
        current_user_id=current_user_id,
        resolution_comment=resolution_comment,
    )
