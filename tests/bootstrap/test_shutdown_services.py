from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from app.bootstrap import shutdown_services


@pytest.mark.asyncio
async def test_shutdown_runtime_task_cancels_task_even_if_stop_call_fails() -> None:
    logger = MagicMock()
    task = asyncio.create_task(asyncio.sleep(60))

    def _failing_stop_call() -> None:
        raise RuntimeError('boom')

    await shutdown_services._shutdown_runtime_task(
        logger,
        task=task,
        info_message='stop-info',
        shutdown_call=_failing_stop_call,
        error_message='stop-error',
    )

    assert task.done()
    logger.info.assert_called_once_with('stop-info')
    logger.error.assert_called_once()
    assert logger.error.call_args.args[0] == 'stop-error'
    assert str(logger.error.call_args.kwargs['error']) == 'boom'


@pytest.mark.asyncio
async def test_shutdown_runtime_task_skips_finished_task() -> None:
    logger = MagicMock()
    task = asyncio.create_task(asyncio.sleep(0))
    await task

    shutdown_call = MagicMock()
    await shutdown_services._shutdown_runtime_task(
        logger,
        task=task,
        info_message='stop-info',
        shutdown_call=shutdown_call,
        error_message='stop-error',
    )

    logger.info.assert_not_called()
    logger.error.assert_not_called()
    shutdown_call.assert_not_called()


@pytest.mark.asyncio
async def test_run_safe_shutdown_calls_forwards_specs_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    logger = MagicMock()
    stop_a = MagicMock()
    stop_b = MagicMock()
    received_calls: list[tuple[object, str, str, object]] = []

    async def _fake_safe_shutdown_call(
        logger_arg: object,
        *,
        info_message: str,
        error_message: str,
        shutdown_call: object,
    ) -> None:
        received_calls.append((logger_arg, info_message, error_message, shutdown_call))

    monkeypatch.setattr(shutdown_services, '_safe_shutdown_call', _fake_safe_shutdown_call)

    await shutdown_services._run_safe_shutdown_calls(
        logger,
        shutdown_calls=(
            ('stop-a', 'error-a', stop_a),
            ('stop-b', 'error-b', stop_b),
        ),
    )

    assert received_calls == [
        (logger, 'stop-a', 'error-a', stop_a),
        (logger, 'stop-b', 'error-b', stop_b),
    ]
