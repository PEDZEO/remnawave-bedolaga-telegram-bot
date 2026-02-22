from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.bootstrap.shutdown_web import shutdown_web_runtime


@pytest.mark.asyncio
async def test_shutdown_web_runtime_calls_all_shutdown_steps() -> None:
    logger = MagicMock()
    bot = MagicMock()
    bot.delete_webhook = AsyncMock()
    bot.session = MagicMock()
    bot.session.close = AsyncMock()
    web_api_server = MagicMock()
    web_api_server.stop = AsyncMock()

    await shutdown_web_runtime(
        logger,
        bot=bot,
        web_api_server=web_api_server,
        telegram_webhook_enabled=True,
    )

    bot.delete_webhook.assert_awaited_once_with(drop_pending_updates=False)
    web_api_server.stop.assert_awaited_once()
    bot.session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_shutdown_web_runtime_handles_exceptions_without_raising() -> None:
    logger = MagicMock()
    bot = MagicMock()
    bot.delete_webhook = AsyncMock(side_effect=RuntimeError('webhook-fail'))
    bot.session = MagicMock()
    bot.session.close = AsyncMock(side_effect=RuntimeError('session-fail'))
    web_api_server = MagicMock()
    web_api_server.stop = AsyncMock(side_effect=RuntimeError('web-api-fail'))

    await shutdown_web_runtime(
        logger,
        bot=bot,
        web_api_server=web_api_server,
        telegram_webhook_enabled=True,
    )

    assert logger.error.call_count == 3
