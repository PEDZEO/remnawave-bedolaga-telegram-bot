"""Admin routes for manual account-linking merge moderation."""

from __future__ import annotations

import math
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Ticket, TicketMessage, User

from ..dependencies import get_cabinet_db, get_current_admin_user
from ..schemas.account_linking import (
    AdminManualMergeItem,
    AdminManualMergeListResponse,
    AdminManualMergeResolveRequest,
)
from ..services.account_linking import (
    LinkCodeConflictError,
    LinkCodeInvalidError,
    get_user_identity_hints,
    manual_merge_users,
)
from ..services.manual_merge_ticket import (
    MANUAL_MERGE_TICKET_TITLE,
    build_manual_merge_resolution_message,
    parse_manual_merge_payload,
    parse_manual_merge_resolution,
)


router = APIRouter(prefix='/admin/account-linking', tags=['Cabinet Admin Account Linking'])


def _link_error_to_http(exc: Exception) -> HTTPException:
    detail = {'code': getattr(exc, 'code', 'link_code_error'), 'message': str(exc)}
    code = detail['code']
    if code in {'link_code_invalid', 'link_code_same_account', 'link_code_user_not_found'}:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if code in {
        'manual_merge_required',
        'link_code_identity_conflict',
        'link_code_source_inactive',
        'link_code_target_inactive',
    }:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _extract_merge_context(ticket: Ticket) -> tuple[int | None, int | None, str | None]:
    """Return (current_user_id, source_user_id, decision)."""
    current_user_id: int | None = None
    source_user_id: int | None = None
    decision: str | None = None

    for message in ticket.messages:
        payload = parse_manual_merge_payload(message.message_text or '')
        if payload:
            current_user_id = payload['current_user_id']
            source_user_id = payload['source_user_id']
        resolution = parse_manual_merge_resolution(message.message_text or '')
        if resolution:
            decision = str(resolution['action'])

    return current_user_id, source_user_id, decision


def _to_item(ticket: Ticket, source_user: User | None = None) -> AdminManualMergeItem:
    current_user_id, source_user_id, decision = _extract_merge_context(ticket)
    user_comment: str | None = None
    resolution_comment: str | None = None

    for message in ticket.messages:
        text = message.message_text or ''
        if not user_comment:
            if 'User comment:' in text:
                user_comment = text.split('User comment:', 1)[1].strip()
            elif 'Комментарий пользователя:' in text:
                user_comment = text.split('Комментарий пользователя:', 1)[1].strip()
        resolution = parse_manual_merge_resolution(text)
        if resolution and resolution.get('comment'):
            resolution_comment = str(resolution['comment'])

    requester_hints = get_user_identity_hints(ticket.user) if ticket.user else {}
    source_hints = get_user_identity_hints(source_user) if source_user else {}

    return AdminManualMergeItem(
        ticket_id=ticket.id,
        status=ticket.status,
        decision=decision,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at or ticket.created_at,
        requester_user_id=ticket.user_id,
        source_user_id=source_user_id,
        current_user_id=current_user_id,
        requester_identity_hints=requester_hints,
        source_identity_hints=source_hints,
        user_comment=user_comment,
        resolution_comment=resolution_comment,
    )


@router.get('/manual-merges', response_model=AdminManualMergeListResponse)
async def get_manual_merges(
    state: str = Query('pending', description='pending|approved|rejected|all'),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """List manual merge requests for moderation."""
    stmt = (
        select(Ticket)
        .where(Ticket.title == MANUAL_MERGE_TICKET_TITLE)
        .options(selectinload(Ticket.messages), selectinload(Ticket.user))
        .order_by(desc(Ticket.created_at))
    )
    result = await db.execute(stmt)
    tickets = list(result.scalars().all())

    filtered: list[Ticket] = []
    for ticket in tickets:
        _, _, decision = _extract_merge_context(ticket)
        if state == 'pending':
            if decision is None:
                filtered.append(ticket)
        elif state == 'approved':
            if decision == 'approve':
                filtered.append(ticket)
        elif state == 'rejected':
            if decision == 'reject':
                filtered.append(ticket)
        else:
            filtered.append(ticket)

    total = len(filtered)
    pages = max(1, math.ceil(total / per_page)) if total else 0
    start = (page - 1) * per_page
    end = start + per_page
    page_tickets = filtered[start:end]

    source_ids = {
        source_user_id
        for ticket in page_tickets
        for source_user_id in [_extract_merge_context(ticket)[1]]
        if source_user_id is not None
    }
    source_users_map: dict[int, User] = {}
    if source_ids:
        users_result = await db.execute(select(User).where(User.id.in_(source_ids)))
        source_users_map = {user.id: user for user in users_result.scalars().all()}

    items = []
    for ticket in page_tickets:
        _, source_user_id, _ = _extract_merge_context(ticket)
        source_user = source_users_map.get(source_user_id) if source_user_id else None
        items.append(_to_item(ticket, source_user=source_user))

    return AdminManualMergeListResponse(items=items, total=total, page=page, per_page=per_page, pages=pages)


@router.post('/manual-merges/{ticket_id}/resolve', response_model=AdminManualMergeItem)
async def resolve_manual_merge(
    ticket_id: int,
    request: AdminManualMergeResolveRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Approve/reject manual merge request."""
    action = request.action.strip().lower()
    if action not in {'approve', 'reject'}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_action', 'message': 'action must be approve or reject'},
        )

    ticket_stmt = (
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(selectinload(Ticket.messages), selectinload(Ticket.user))
        .with_for_update()
    )
    ticket_result = await db.execute(ticket_stmt)
    ticket = ticket_result.scalar_one_or_none()
    if ticket is None or ticket.title != MANUAL_MERGE_TICKET_TITLE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'manual_merge_ticket_not_found', 'message': 'Manual merge ticket not found'},
        )

    current_user_id, source_user_id, decision = _extract_merge_context(ticket)
    if current_user_id is None or source_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'manual_merge_payload_missing',
                'message': 'Cannot parse merge payload from ticket',
            },
        )
    if decision is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'code': 'manual_merge_already_resolved', 'message': 'Manual merge already resolved'},
        )

    primary_user_id: int | None = None
    secondary_user_id: int | None = None

    if action == 'approve':
        if request.primary_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'primary_user_required',
                    'message': 'primary_user_id is required for approve action',
                },
            )
        if request.primary_user_id not in {current_user_id, source_user_id}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'invalid_primary_user',
                    'message': 'primary_user_id must be one of merge participants',
                },
            )
        primary_user_id = request.primary_user_id
        secondary_user_id = source_user_id if primary_user_id == current_user_id else current_user_id
        try:
            await manual_merge_users(
                db,
                primary_user_id=primary_user_id,
                secondary_user_id=secondary_user_id,
                commit=False,
            )
        except (LinkCodeConflictError, LinkCodeInvalidError) as exc:
            await db.rollback()
            raise _link_error_to_http(exc) from exc

    resolution_message = build_manual_merge_resolution_message(
        action=action,
        admin_user_id=admin.id,
        primary_user_id=primary_user_id,
        secondary_user_id=secondary_user_id,
        comment=request.comment,
    )
    db.add(
        TicketMessage(
            ticket_id=ticket.id,
            user_id=admin.id,
            message_text=resolution_message,
            is_from_admin=True,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
    )
    ticket.status = 'closed'
    ticket.closed_at = datetime.now(UTC).replace(tzinfo=None)
    ticket.updated_at = datetime.now(UTC).replace(tzinfo=None)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'code': 'manual_merge_commit_failed', 'message': 'Failed to persist merge resolution'},
        ) from exc

    await db.refresh(ticket)
    source_user: User | None = None
    if source_user_id:
        source_result = await db.execute(select(User).where(User.id == source_user_id))
        source_user = source_result.scalar_one_or_none()
    messages_result = await db.execute(
        select(Ticket)
        .where(Ticket.id == ticket.id)
        .options(selectinload(Ticket.messages), selectinload(Ticket.user))
    )
    fresh_ticket = messages_result.scalar_one()
    return _to_item(fresh_ticket, source_user=source_user)
