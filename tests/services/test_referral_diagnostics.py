"""
Тесты для сервиса диагностики реферальной системы.
"""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.referral_diagnostics_service import ReferralDiagnosticsService


@pytest.fixture
def temp_log_file():
    """Создаёт временный лог-файл для тестов."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        yield Path(f.name)
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_log_content():
    """Пример содержимого лог-файла с реферальными событиями."""
    today = datetime.now(UTC).strftime('%Y-%m-%d')
    return f"""
{today} 10:00:00,123 - app.handlers.start - INFO - 📩 Сообщение от ID:123456789 username:test /start refABC123
{today} 10:00:05,456 - app.handlers.start - INFO - 💾 Сохранен start payload 'refXYZ999' для пользователя 987654321
{today} 12:00:00,901 - app.handlers.start - INFO - 📩 Сообщение от ID:111111111 username:test2 /start refTEST777

{today} 13:00:00,234 - unrelated module - INFO - Some other log message
"""


@pytest.mark.asyncio
async def test_parse_logs_basic(temp_log_file, sample_log_content):
    """Тест базового парсинга реф-кликов из логов."""
    temp_log_file.write_text(sample_log_content)

    service = ReferralDiagnosticsService(log_path=str(temp_log_file))

    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    clicks, total_lines, lines_in_period = await service._parse_clicks(today, tomorrow)

    assert total_lines >= 3
    assert lines_in_period >= 3
    assert len(clicks) == 3
    assert {c.telegram_id for c in clicks} == {123456789, 987654321, 111111111}
    assert {c.clean_code for c in clicks} == {'refABC123', 'refXYZ999', 'refTEST777'}


class _MockScalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _MockResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _MockScalars(self._rows)


@pytest.mark.asyncio
async def test_analyze_period_with_issues(temp_log_file, sample_log_content):
    """Тест анализа с проблемными случаями."""
    temp_log_file.write_text(sample_log_content)

    service = ReferralDiagnosticsService(log_path=str(temp_log_file))

    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    user_ok = SimpleNamespace(
        id=1,
        telegram_id=123456789,
        username='ok',
        full_name='OK User',
        created_at=today + timedelta(hours=1),
        referred_by_id=100,
    )
    ref_abc = SimpleNamespace(id=100, referral_code='refABC123', full_name='Ref A')
    ref_xyz = SimpleNamespace(id=101, referral_code='refXYZ999', full_name='Ref X')
    ref_test = SimpleNamespace(id=102, referral_code='refTEST777', full_name='Ref T')

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[_MockResult([user_ok]), _MockResult([ref_abc, ref_xyz, ref_test])])

    report = await service.analyze_period(mock_db, today, tomorrow)

    assert report.total_ref_clicks == 3
    assert report.unique_users_clicked == 3
    lost_ids = {item.telegram_id for item in report.lost_referrals}
    assert 987654321 in lost_ids
    assert 111111111 in lost_ids


@pytest.mark.asyncio
async def test_empty_log_file(temp_log_file):
    """Тест работы с пустым лог-файлом."""
    temp_log_file.write_text('')

    service = ReferralDiagnosticsService(log_path=str(temp_log_file))

    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[_MockResult([]), _MockResult([])])

    report = await service.analyze_period(mock_db, today, tomorrow)

    assert report.total_ref_clicks == 0
    assert report.unique_users_clicked == 0
    assert len(report.lost_referrals) == 0


@pytest.mark.asyncio
async def test_nonexistent_log_file():
    """Тест работы с несуществующим лог-файлом."""
    service = ReferralDiagnosticsService(log_path='/nonexistent/path/to/log.log')

    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[_MockResult([]), _MockResult([])])

    report = await service.analyze_period(mock_db, today, tomorrow)

    assert report.total_ref_clicks == 0
    assert len(report.lost_referrals) == 0


@pytest.mark.asyncio
async def test_analyze_today(temp_log_file, sample_log_content):
    """Тест метода analyze_today."""
    temp_log_file.write_text(sample_log_content)

    service = ReferralDiagnosticsService(log_path=str(temp_log_file))

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[_MockResult([]), _MockResult([])])

    report = await service.analyze_today(mock_db)

    # Проверяем что период установлен корректно
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    assert report.analysis_period_start.date() == today.date()
