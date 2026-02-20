"""Admin routes for live bot menu layout management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.cabinet.dependencies import get_cabinet_db, get_current_admin_user
from app.config import settings
from app.database.models import User
from app.services.menu_layout_service import MenuLayoutService
from app.webapi.schemas.menu_layout import (
    ButtonConditions,
    ButtonUpdateRequest,
    MenuButtonConfig,
    MenuLayoutResponse,
    MenuLayoutUpdateRequest,
    MenuRowConfig,
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
                updates['conditions'] = {key: value for key, value in updates['conditions'].items() if value is not None}

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
