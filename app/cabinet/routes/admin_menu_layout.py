"""Admin routes for live bot menu layout management."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.cabinet.dependencies import get_cabinet_db, get_current_admin_user
from app.config import settings
from app.database.models import User
from app.services.menu_layout_service import MenuLayoutService
from app.webapi.schemas.menu_layout import (
    ButtonClickStats,
    ButtonClickStatsResponse,
    ButtonConditions,
    ButtonTypeStats,
    ButtonTypeStatsResponse,
    ButtonUpdateRequest,
    HourlyStats,
    HourlyStatsResponse,
    MenuButtonConfig,
    MenuClickStatsResponse,
    MenuLayoutResponse,
    MenuLayoutUpdateRequest,
    MenuRowConfig,
    PeriodComparisonResponse,
    TopUsersResponse,
    TopUserStats,
    UserClickSequence,
    UserClickSequencesResponse,
    WeekdayStats,
    WeekdayStatsResponse,
)


router = APIRouter(prefix='/admin/menu-layout', tags=['Admin Menu Layout'])


def _serialize_config(config: dict[str, Any], is_enabled: bool, updated_at: Any) -> MenuLayoutResponse:
    rows = [
        MenuRowConfig(
            id=row_data['id'],
            buttons=row_data.get('buttons', []),
            conditions=ButtonConditions(**row_data['conditions']) if row_data.get('conditions') else None,
            max_per_row=row_data.get('max_per_row', 2),
        )
        for row_data in config.get('rows', [])
    ]

    buttons: dict[str, MenuButtonConfig] = {}
    for button_id, button_data in config.get('buttons', {}).items():
        buttons[button_id] = MenuButtonConfig(
            type=button_data['type'],
            builtin_id=button_data.get('builtin_id'),
            text=button_data.get('text', {}),
            icon=button_data.get('icon'),
            action=button_data.get('action', ''),
            enabled=button_data.get('enabled', True),
            visibility=button_data.get('visibility', 'all'),
            conditions=ButtonConditions(**button_data['conditions']) if button_data.get('conditions') else None,
            dynamic_text=button_data.get('dynamic_text', False),
            open_mode=button_data.get('open_mode', 'callback'),
            webapp_url=button_data.get('webapp_url'),
            description=button_data.get('description'),
            sort_order=button_data.get('sort_order'),
        )

    return MenuLayoutResponse(
        version=config.get('version', 1),
        rows=rows,
        buttons=buttons,
        is_enabled=is_enabled,
        updated_at=updated_at,
    )


@router.get('', response_model=MenuLayoutResponse)
async def get_menu_layout(
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> MenuLayoutResponse:
    _ = admin
    config = await MenuLayoutService.get_config(db)
    updated_at = await MenuLayoutService.get_config_updated_at(db)
    return _serialize_config(config, settings.MENU_LAYOUT_ENABLED, updated_at)


@router.put('', response_model=MenuLayoutResponse)
async def update_menu_layout(
    payload: MenuLayoutUpdateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> MenuLayoutResponse:
    _ = admin

    config = await MenuLayoutService.get_config(db)
    updated = config.copy()

    if payload.rows is not None:
        updated['rows'] = [row.model_dump(exclude_none=True) for row in payload.rows]

    if payload.buttons is not None:
        updated['buttons'] = {
            button_id: button.model_dump(exclude_none=True) for button_id, button in payload.buttons.items()
        }

    await MenuLayoutService.save_config(db, updated)
    updated_at = await MenuLayoutService.get_config_updated_at(db)
    return _serialize_config(updated, settings.MENU_LAYOUT_ENABLED, updated_at)


@router.patch('/buttons/{button_id}', response_model=MenuButtonConfig)
async def update_menu_button(
    button_id: str,
    payload: ButtonUpdateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> MenuButtonConfig:
    _ = admin
    try:
        updates = payload.model_dump(exclude_unset=True)

        if 'visibility' in updates and updates['visibility'] is not None and hasattr(updates['visibility'], 'value'):
            updates['visibility'] = updates['visibility'].value

        if 'open_mode' in updates and updates['open_mode'] is not None and hasattr(updates['open_mode'], 'value'):
            updates['open_mode'] = updates['open_mode'].value

        if 'conditions' in updates and updates['conditions'] is not None:
            if hasattr(updates['conditions'], 'model_dump'):
                updates['conditions'] = updates['conditions'].model_dump(exclude_none=True)
            elif isinstance(updates['conditions'], dict):
                updates['conditions'] = {
                    key: value for key, value in updates['conditions'].items() if value is not None
                }

        button = await MenuLayoutService.update_button(db, button_id, updates)
        return MenuButtonConfig(
            type=button['type'],
            builtin_id=button.get('builtin_id'),
            text=button.get('text', {}),
            icon=button.get('icon'),
            action=button.get('action', ''),
            enabled=button.get('enabled', True),
            visibility=button.get('visibility', 'all'),
            conditions=ButtonConditions(**button['conditions']) if button.get('conditions') else None,
            dynamic_text=button.get('dynamic_text', False),
            open_mode=button.get('open_mode', 'callback'),
            webapp_url=button.get('webapp_url'),
            description=button.get('description'),
            sort_order=button.get('sort_order'),
        )
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get('/stats', response_model=MenuClickStatsResponse)
async def get_menu_click_stats(
    days: int = 30,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> MenuClickStatsResponse:
    _ = admin
    stats = await MenuLayoutService.get_all_buttons_stats(db, days)
    total_clicks = await MenuLayoutService.get_total_clicks(db, days)

    now = datetime.now(UTC)
    period_start = now - timedelta(days=days)

    return MenuClickStatsResponse(
        items=[
            ButtonClickStats(
                button_id=entry['button_id'],
                clicks_total=entry['clicks_total'],
                clicks_today=entry.get('clicks_today', 0),
                clicks_week=entry.get('clicks_week', 0),
                clicks_month=entry.get('clicks_month', 0),
                unique_users=entry['unique_users'],
                last_click_at=entry['last_click_at'],
            )
            for entry in stats
        ],
        total_clicks=total_clicks,
        period_start=period_start,
        period_end=now,
    )


@router.get('/stats/buttons/{button_id}', response_model=ButtonClickStatsResponse)
async def get_button_click_stats(
    button_id: str,
    days: int = 30,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> ButtonClickStatsResponse:
    _ = admin
    stats = await MenuLayoutService.get_button_stats(db, button_id, days)
    clicks_by_day = await MenuLayoutService.get_button_clicks_by_day(db, button_id, days)

    return ButtonClickStatsResponse(
        button_id=button_id,
        stats=ButtonClickStats(
            button_id=stats['button_id'],
            clicks_total=stats['clicks_total'],
            clicks_today=stats['clicks_today'],
            clicks_week=stats['clicks_week'],
            clicks_month=stats['clicks_month'],
            unique_users=stats['unique_users'],
            last_click_at=stats['last_click_at'],
        ),
        clicks_by_day=clicks_by_day,
    )


@router.get('/stats/by-type', response_model=ButtonTypeStatsResponse)
async def get_stats_by_button_type(
    days: int = 30,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> ButtonTypeStatsResponse:
    _ = admin
    stats = await MenuLayoutService.get_stats_by_button_type(db, days)
    total_clicks = sum(entry['clicks_total'] for entry in stats)

    return ButtonTypeStatsResponse(
        items=[
            ButtonTypeStats(
                button_type=entry['button_type'],
                clicks_total=entry['clicks_total'],
                unique_users=entry['unique_users'],
            )
            for entry in stats
        ],
        total_clicks=total_clicks,
    )


@router.get('/stats/by-hour', response_model=HourlyStatsResponse)
async def get_clicks_by_hour(
    button_id: str | None = None,
    days: int = 30,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> HourlyStatsResponse:
    _ = admin
    stats = await MenuLayoutService.get_clicks_by_hour(db, button_id, days)
    return HourlyStatsResponse(
        items=[HourlyStats(hour=entry['hour'], count=entry['count']) for entry in stats], button_id=button_id
    )


@router.get('/stats/by-weekday', response_model=WeekdayStatsResponse)
async def get_clicks_by_weekday(
    button_id: str | None = None,
    days: int = 30,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> WeekdayStatsResponse:
    _ = admin
    stats = await MenuLayoutService.get_clicks_by_weekday(db, button_id, days)
    return WeekdayStatsResponse(
        items=[
            WeekdayStats(weekday=entry['weekday'], weekday_name=entry['weekday_name'], count=entry['count'])
            for entry in stats
        ],
        button_id=button_id,
    )


@router.get('/stats/top-users', response_model=TopUsersResponse)
async def get_top_users(
    button_id: str | None = None,
    limit: int = 10,
    days: int = 30,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> TopUsersResponse:
    _ = admin
    stats = await MenuLayoutService.get_top_users(db, button_id, limit, days)
    return TopUsersResponse(
        items=[
            TopUserStats(
                user_id=entry['user_id'],
                clicks_count=entry['clicks_count'],
                last_click_at=entry['last_click_at'],
            )
            for entry in stats
        ],
        button_id=button_id,
        limit=limit,
    )


@router.get('/stats/compare', response_model=PeriodComparisonResponse)
async def get_period_comparison(
    button_id: str | None = None,
    current_days: int = 7,
    previous_days: int = 7,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> PeriodComparisonResponse:
    _ = admin
    comparison = await MenuLayoutService.get_period_comparison(db, button_id, current_days, previous_days)
    return PeriodComparisonResponse(
        current_period=comparison['current_period'],
        previous_period=comparison['previous_period'],
        change=comparison['change'],
        button_id=button_id,
    )


@router.get('/stats/users/{user_id}/sequences', response_model=UserClickSequencesResponse)
async def get_user_click_sequences(
    user_id: int,
    limit: int = 50,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> UserClickSequencesResponse:
    _ = admin
    sequences = await MenuLayoutService.get_user_click_sequences(db, user_id, limit)
    return UserClickSequencesResponse(
        user_id=user_id,
        items=[
            UserClickSequence(
                button_id=entry['button_id'],
                button_text=entry.get('button_text'),
                clicked_at=entry['clicked_at'],
            )
            for entry in sequences
        ],
        total=len(sequences),
    )
