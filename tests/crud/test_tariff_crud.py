from unittest.mock import AsyncMock

import pytest

from app.database.crud.tariff import create_tariff, update_tariff


pytestmark = pytest.mark.asyncio


async def test_create_tariff_persists_external_squad_uuid(mock_db_session):
    tariff = await create_tariff(
        db=mock_db_session,
        name='Test Tariff',
        external_squad_uuid='123e4567-e89b-12d3-a456-426614174000',
    )

    assert tariff.external_squad_uuid == '123e4567-e89b-12d3-a456-426614174000'
    mock_db_session.add.assert_called_once()
    mock_db_session.flush.assert_awaited_once()
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once()


async def test_update_tariff_updates_external_squad_uuid(mock_db_session):
    tariff = await create_tariff(
        db=mock_db_session,
        name='Update Tariff',
    )

    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    updated = await update_tariff(
        db=mock_db_session,
        tariff=tariff,
        external_squad_uuid='123e4567-e89b-12d3-a456-426614174001',
    )

    assert updated.external_squad_uuid == '123e4567-e89b-12d3-a456-426614174001'
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(tariff)
