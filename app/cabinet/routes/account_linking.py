"""Account linking routes for cabinet authentication."""

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.user import get_user_by_id
from app.database.models import Ticket, TicketMessage, User, UserStatus
from app.handlers.tickets import notify_admins_about_new_ticket

from ..dependencies import get_cabinet_db, get_current_cabinet_user
from ..schemas.account_linking import (
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
from .auth import _create_auth_response, _store_refresh_token


logger = structlog.get_logger(__name__)
router = APIRouter(prefix='/auth', tags=['Cabinet Account Linking'])


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


@router.get('/identities', response_model=LinkedIdentitiesResponse)
async def get_linked_identities(user: User = Depends(get_current_cabinet_user)):
    """Get linked login identities for current user."""
    hints = get_user_identity_hints(user)
    identities = [
        LinkedIdentity(provider=provider, provider_user_id_masked=provider_user_id_masked)
        for provider, provider_user_id_masked in sorted(hints.items())
    ]
    return LinkedIdentitiesResponse(identities=identities)


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

    title = 'Manual account merge request'
    message_lines = [
        'User requested manual merge for disputed account-linking case.',
        f'Current user id: {user.id}',
        f'Code source user id: {source_user.id}',
        f'Current user identities: {get_user_identity_hints(user)}',
        f'Source user identities: {get_user_identity_hints(source_user)}',
    ]
    if request.comment:
        message_lines.append(f'User comment: {request.comment}')
    message_text = '\n'.join(message_lines)

    ticket = Ticket(
        user_id=user.id,
        title=title,
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
