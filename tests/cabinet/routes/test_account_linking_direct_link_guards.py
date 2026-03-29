from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.cabinet.auth.oauth_providers import OAuthUserInfo


pytestmark = pytest.mark.asyncio


def _load_account_linking_module():
    module_name = 'app.cabinet.routes.account_linking'
    if module_name in sys.modules:
        return sys.modules[module_name]

    routes_package_name = 'app.cabinet.routes'
    if routes_package_name not in sys.modules:
        routes_package = types.ModuleType(routes_package_name)
        routes_package.__path__ = [str(Path(__file__).resolve().parents[3] / 'app' / 'cabinet' / 'routes')]
        sys.modules[routes_package_name] = routes_package

    module_path = Path(__file__).resolve().parents[3] / 'app' / 'cabinet' / 'routes' / 'account_linking.py'
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError('Failed to load account_linking module for tests')

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


account_linking = _load_account_linking_module()


def build_user(user_id: int, *, telegram_id: int | None = None, email: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        telegram_id=telegram_id,
        first_name=None,
        last_name=None,
        username=None,
        email=email,
        email_verified=False,
        email_verified_at=None,
        updated_at=None,
        auth_type='email',
    )


def build_user_info(
    *,
    provider: str = 'yandex',
    provider_id: str = 'provider-1',
    email: str | None = None,
    email_verified: bool = False,
) -> OAuthUserInfo:
    return OAuthUserInfo(
        provider=provider,
        provider_id=provider_id,
        email=email,
        email_verified=email_verified,
        username='linked-user',
        first_name='Linked',
        last_name='User',
    )


async def test_link_oauth_identity_rejects_provider_owned_by_other_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = build_user(1)
    foreign_user = build_user(2)

    monkeypatch.setattr(
        account_linking,
        'get_user_by_oauth_provider',
        AsyncMock(return_value=foreign_user),
    )
    monkeypatch.setattr(account_linking, 'get_user_by_email', AsyncMock(return_value=None))
    set_provider_mock = AsyncMock()
    monkeypatch.setattr(account_linking, 'set_user_oauth_provider_id', set_provider_mock)

    with pytest.raises(HTTPException) as exc_info:
        await account_linking._link_oauth_identity(
            SimpleNamespace(),
            user=current_user,
            provider='yandex',
            user_info=build_user_info(provider_id='ya-1'),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail['code'] == 'link_code_identity_conflict'
    set_provider_mock.assert_not_awaited()


async def test_link_oauth_identity_rejects_verified_email_owned_by_other_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = build_user(1, email='current@example.com')
    foreign_user = build_user(2, email='shared@example.com')

    monkeypatch.setattr(account_linking, 'get_user_by_oauth_provider', AsyncMock(return_value=None))
    monkeypatch.setattr(
        account_linking,
        'get_user_by_email',
        AsyncMock(return_value=foreign_user),
    )
    set_provider_mock = AsyncMock()
    monkeypatch.setattr(account_linking, 'set_user_oauth_provider_id', set_provider_mock)

    with pytest.raises(HTTPException) as exc_info:
        await account_linking._link_oauth_identity(
            SimpleNamespace(),
            user=current_user,
            provider='google',
            user_info=build_user_info(
                provider_id='google-1',
                email='shared@example.com',
                email_verified=True,
            ),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail['code'] == 'link_code_identity_conflict'
    set_provider_mock.assert_not_awaited()


async def test_link_oauth_identity_keeps_same_user_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = build_user(7, email='same@example.com')

    monkeypatch.setattr(
        account_linking,
        'get_user_by_oauth_provider',
        AsyncMock(return_value=current_user),
    )
    monkeypatch.setattr(account_linking, 'get_user_by_email', AsyncMock(return_value=None))
    set_provider_mock = AsyncMock()
    monkeypatch.setattr(account_linking, 'set_user_oauth_provider_id', set_provider_mock)

    result = await account_linking._link_oauth_identity(
        SimpleNamespace(),
        user=current_user,
        provider='vk',
        user_info=build_user_info(provider_id='vk-1'),
    )

    assert result is current_user
    set_provider_mock.assert_awaited_once()


async def test_link_telegram_identity_rejects_foreign_telegram(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_user = build_user(1)
    foreign_user = build_user(2, telegram_id=777)

    monkeypatch.setattr(
        account_linking,
        'get_user_by_telegram_id',
        AsyncMock(return_value=foreign_user),
    )
    monkeypatch.setattr(account_linking, '_ensure_telegram_attach_allowed', AsyncMock())
    monkeypatch.setattr(account_linking, '_ensure_telegram_relink_allowed', AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await account_linking._link_telegram_identity(
            SimpleNamespace(),
            user=current_user,
            telegram_id=777,
            user_data={'id': 777, 'username': 'linked'},
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail['code'] == 'link_code_identity_conflict'
