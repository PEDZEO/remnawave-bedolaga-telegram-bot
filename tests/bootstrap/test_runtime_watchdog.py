from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from app.bootstrap.runtime_watchdog import _restart_task_on_exception


@pytest.mark.asyncio
async def test_restart_task_on_exception_returns_original_when_task_is_none() -> None:
    logger = MagicMock()

    result = _restart_task_on_exception(logger, None, error_message='boom')

    assert result is None
    logger.error.assert_not_called()


@pytest.mark.asyncio
async def test_restart_task_on_exception_returns_original_when_no_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    logger = MagicMock()
    task = MagicMock()
    task.done.return_value = True
    task.exception.return_value = None
    create_task = MagicMock()
    monkeypatch.setattr(asyncio, 'create_task', create_task)

    result = _restart_task_on_exception(
        logger,
        task,
        error_message='boom',
        restart_factory=MagicMock(),
    )

    assert result is task
    create_task.assert_not_called()
    logger.error.assert_not_called()


@pytest.mark.asyncio
async def test_restart_task_on_exception_restarts_task_when_condition_allows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = MagicMock()
    task = MagicMock()
    task.done.return_value = True
    task.exception.return_value = RuntimeError('fail')

    restart_factory = MagicMock(return_value=MagicMock())

    created_task = MagicMock()
    create_task = MagicMock(return_value=created_task)
    monkeypatch.setattr(asyncio, 'create_task', create_task)

    result = _restart_task_on_exception(
        logger,
        task,
        error_message='service failed',
        restart_factory=restart_factory,
        restart_message='restart',
        restart_condition=lambda: True,
    )

    assert result is created_task
    logger.error.assert_called_once()
    logger.info.assert_called_once_with('restart')
    create_task.assert_called_once()


@pytest.mark.asyncio
async def test_restart_task_on_exception_does_not_restart_when_condition_denies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = MagicMock()
    task = MagicMock()
    task.done.return_value = True
    task.exception.return_value = RuntimeError('fail')

    restart_factory = MagicMock(return_value=MagicMock())

    create_task = MagicMock()
    monkeypatch.setattr(asyncio, 'create_task', create_task)

    result = _restart_task_on_exception(
        logger,
        task,
        error_message='service failed',
        restart_factory=restart_factory,
        restart_message='restart',
        restart_condition=lambda: False,
    )

    assert result is task
    logger.error.assert_called_once()
    logger.info.assert_not_called()
    create_task.assert_not_called()
