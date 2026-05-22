"""Admin Ultima overview and diagnostics routes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cabinet.dependencies import get_cabinet_db, require_permission
from app.config import settings
from app.database.models import Ticket, User
from app.services.ultima_start_service import (
    UltimaNotificationButton,
    get_ultima_notification_config,
    get_ultima_start_config,
    is_ultima_mode_enabled,
    is_ultima_start_button_usable,
)


router = APIRouter(prefix='/admin/ultima', tags=['Admin Ultima'])

DiagnosticStatus = Literal['ok', 'warning', 'error']


class UltimaOverviewMode(BaseModel):
    enabled: bool
    main_menu_mode: str
    account_linking_mode: str


class UltimaOverviewStart(BaseModel):
    enabled: bool
    message_text: str
    button_text: str
    button_url: str
    fallback_to_regular_menu: bool


class UltimaOverviewSupport(BaseModel):
    support_type: str
    tickets_enabled: bool
    miniapp_tickets_enabled: bool
    global_tickets_enabled: bool
    support_username: str | None = None
    support_url: str | None = None
    channel_label: str


class UltimaOverviewNotificationButton(BaseModel):
    text: str
    path: str


class UltimaOverviewNotifications(BaseModel):
    enabled: bool
    buttons: list[UltimaOverviewNotificationButton]


class UltimaOverviewConfig(BaseModel):
    miniapp_url: str
    purchase_url: str
    static_path: str
    service_name_ru: str
    service_name_en: str


class UltimaOverviewDiagnostic(BaseModel):
    key: str
    label: str
    status: DiagnosticStatus
    message: str


class UltimaOverviewMetrics(BaseModel):
    tickets_total: int
    tickets_open: int
    tickets_pending: int
    tickets_answered: int
    tickets_closed: int
    tickets_created_7d: int


class UltimaOverviewResponse(BaseModel):
    status: DiagnosticStatus
    mode: UltimaOverviewMode
    start: UltimaOverviewStart
    support: UltimaOverviewSupport
    notifications: UltimaOverviewNotifications
    config: UltimaOverviewConfig
    diagnostics: list[UltimaOverviewDiagnostic]
    metrics: UltimaOverviewMetrics


def _is_http_url(value: str | None) -> bool:
    raw = (value or '').strip()
    return raw.startswith(('http://', 'https://'))


def _diagnostic_status(items: list[UltimaOverviewDiagnostic]) -> DiagnosticStatus:
    if any(item.status == 'error' for item in items):
        return 'error'
    if any(item.status == 'warning' for item in items):
        return 'warning'
    return 'ok'


def _notification_button_to_response(button: UltimaNotificationButton) -> UltimaOverviewNotificationButton:
    return UltimaOverviewNotificationButton(text=button.text, path=button.path)


async def _count_tickets(db: AsyncSession, status: str | None = None, since: datetime | None = None) -> int:
    query = select(func.count()).select_from(Ticket)
    if status is not None:
        query = query.where(Ticket.status == status)
    if since is not None:
        query = query.where(Ticket.created_at >= since)
    result = await db.execute(query)
    return int(result.scalar() or 0)


@router.get('/overview', response_model=UltimaOverviewResponse)
async def get_ultima_overview(
    admin: User = Depends(require_permission('settings:read')),
    db: AsyncSession = Depends(get_cabinet_db),
) -> UltimaOverviewResponse:
    """Return a single admin-facing Ultima status, preview and diagnostics payload."""
    _ = admin
    ultima_enabled = await is_ultima_mode_enabled(db)
    start_config = await get_ultima_start_config(db)
    notification_config = await get_ultima_notification_config(db)

    support_type = settings.get_miniapp_support_type()
    miniapp_tickets_enabled = settings.is_miniapp_tickets_enabled()
    global_tickets_enabled = settings.is_support_tickets_enabled()
    tickets_enabled = miniapp_tickets_enabled and global_tickets_enabled and support_type in {'tickets', 'both'}
    effective_support_type = support_type
    if support_type in {'tickets', 'both'} and not tickets_enabled:
        effective_support_type = 'profile'

    support_url = settings.get_miniapp_support_url() if effective_support_type == 'url' else None
    support_username = (settings.SUPPORT_USERNAME or '').strip() or None
    channel_label = {
        'tickets': 'Tickets',
        'both': 'Tickets + Telegram profile',
        'profile': 'Telegram profile',
        'url': 'External URL',
    }.get(effective_support_type, effective_support_type)

    diagnostics: list[UltimaOverviewDiagnostic] = []
    diagnostics.append(
        UltimaOverviewDiagnostic(
            key='ultima_mode',
            label='Ultima mode',
            status='ok' if ultima_enabled else 'warning',
            message='Ultima mode is enabled.' if ultima_enabled else 'Ultima mode is disabled for users.',
        )
    )

    miniapp_url = (settings.MINIAPP_CUSTOM_URL or '').strip()
    diagnostics.append(
        UltimaOverviewDiagnostic(
            key='miniapp_url',
            label='Miniapp URL',
            status='ok' if _is_http_url(miniapp_url) else 'error',
            message='Miniapp URL is configured.' if _is_http_url(miniapp_url) else 'MINIAPP_CUSTOM_URL is missing.',
        )
    )

    start_button_usable = is_ultima_start_button_usable(start_config)
    if start_config.enabled:
        start_status: DiagnosticStatus = 'ok' if start_button_usable else 'warning'
        start_message = (
            'Custom Ultima /start message is enabled.'
            if start_status == 'ok'
            else 'Custom Ultima /start is enabled, but button URL is not usable; regular menu is used.'
        )
    else:
        start_status = 'ok'
        start_message = 'Custom Ultima /start is disabled; bot uses the regular menu.'
    diagnostics.append(
        UltimaOverviewDiagnostic(
            key='start_message',
            label='/start behavior',
            status=start_status,
            message=start_message,
        )
    )

    support_status: DiagnosticStatus = 'ok'
    support_message = f'Support channel: {channel_label}.'
    if support_type == 'url' and not _is_http_url(settings.get_miniapp_support_url()):
        support_status = 'error'
        support_message = 'Support type is URL, but MINIAPP_SUPPORT_URL is missing or invalid.'
    elif support_type in {'tickets', 'both'} and not tickets_enabled:
        support_status = 'warning'
        support_message = 'Tickets were requested, but ticket support is disabled; users fall back to profile.'
    elif effective_support_type in {'profile', 'both'} and not support_username:
        support_status = 'warning'
        support_message = 'Telegram support profile is not configured.'
    diagnostics.append(
        UltimaOverviewDiagnostic(
            key='support',
            label='Support channel',
            status=support_status,
            message=support_message,
        )
    )

    diagnostics.append(
        UltimaOverviewDiagnostic(
            key='notification_buttons',
            label='Notification buttons',
            status='ok' if notification_config.enabled and notification_config.buttons else 'warning',
            message=(
                f'{len(notification_config.buttons)} Ultima notification buttons are configured.'
                if notification_config.enabled
                else 'Ultima notification buttons are disabled.'
            ),
        )
    )

    purchase_url = (settings.MINIAPP_PURCHASE_URL or '').strip()
    diagnostics.append(
        UltimaOverviewDiagnostic(
            key='purchase_url',
            label='Purchase URL',
            status='ok' if not purchase_url or _is_http_url(purchase_url) else 'warning',
            message='Purchase URL is valid.' if purchase_url else 'Purchase URL is empty; main miniapp URL is used.',
        )
    )

    since = datetime.now(UTC) - timedelta(days=7)
    metrics = UltimaOverviewMetrics(
        tickets_total=await _count_tickets(db),
        tickets_open=await _count_tickets(db, 'open'),
        tickets_pending=await _count_tickets(db, 'pending'),
        tickets_answered=await _count_tickets(db, 'answered'),
        tickets_closed=await _count_tickets(db, 'closed'),
        tickets_created_7d=await _count_tickets(db, since=since),
    )

    return UltimaOverviewResponse(
        status=_diagnostic_status(diagnostics),
        mode=UltimaOverviewMode(
            enabled=ultima_enabled,
            main_menu_mode=settings.get_main_menu_mode(),
            account_linking_mode=settings.CABINET_ULTIMA_ACCOUNT_LINKING_MODE,
        ),
        start=UltimaOverviewStart(
            enabled=start_config.enabled,
            message_text=start_config.message_text,
            button_text=start_config.button_text,
            button_url=start_config.button_url,
            fallback_to_regular_menu=not start_config.enabled or not start_button_usable,
        ),
        support=UltimaOverviewSupport(
            support_type=effective_support_type,
            tickets_enabled=tickets_enabled,
            miniapp_tickets_enabled=miniapp_tickets_enabled,
            global_tickets_enabled=global_tickets_enabled,
            support_username=support_username,
            support_url=support_url,
            channel_label=channel_label,
        ),
        notifications=UltimaOverviewNotifications(
            enabled=notification_config.enabled,
            buttons=[_notification_button_to_response(button) for button in notification_config.buttons],
        ),
        config=UltimaOverviewConfig(
            miniapp_url=miniapp_url,
            purchase_url=purchase_url,
            static_path=settings.MINIAPP_STATIC_PATH,
            service_name_ru=settings.MINIAPP_SERVICE_NAME_RU,
            service_name_en=settings.MINIAPP_SERVICE_NAME_EN,
        ),
        diagnostics=diagnostics,
        metrics=metrics,
    )
