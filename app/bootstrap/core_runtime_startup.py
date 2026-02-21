from dataclasses import dataclass
from typing import Any

from aiogram import Bot, Dispatcher

from app.bootstrap.backup_startup import initialize_backup_stage
from app.bootstrap.bot_startup import setup_bot_stage
from app.bootstrap.configuration_startup import load_bot_configuration_stage
from app.bootstrap.contest_rotation_startup import initialize_contest_rotation_stage
from app.bootstrap.database_initialization import initialize_database_stage
from app.bootstrap.database_startup import run_database_migration_stage
from app.bootstrap.external_admin_startup import initialize_external_admin_stage
from app.bootstrap.log_rotation_startup import initialize_log_rotation_stage
from app.bootstrap.nalogo_queue_startup import start_nalogo_queue_stage
from app.bootstrap.payment_methods_startup import initialize_payment_methods_stage
from app.bootstrap.payment_runtime import setup_payment_runtime
from app.bootstrap.payment_verification_startup import initialize_payment_verification_stage
from app.bootstrap.referral_contests_startup import initialize_referral_contests_stage
from app.bootstrap.remnawave_sync_startup import initialize_remnawave_sync_stage
from app.bootstrap.reporting_startup import initialize_reporting_stage
from app.bootstrap.runtime_mode import resolve_runtime_mode
from app.bootstrap.servers_startup import sync_servers_stage
from app.bootstrap.services_startup import connect_integration_services_stage, wire_core_services
from app.bootstrap.tariffs_startup import sync_tariffs_stage
from app.bootstrap.telegram_webhook_startup import configure_telegram_webhook_stage
from app.bootstrap.web_server_startup import start_web_server_stage
from app.config import settings


@dataclass
class CoreRuntimeStartupContext:
    bot: Bot
    dp: Dispatcher
    payment_service: Any
    verification_providers: list[str]
    auto_verification_active: bool
    polling_enabled: bool
    telegram_webhook_enabled: bool
    web_api_server: Any


async def start_core_runtime_stage(timeline, logger, telegram_notifier) -> CoreRuntimeStartupContext:
    await run_database_migration_stage(timeline, logger)
    await initialize_database_stage(timeline)
    await sync_tariffs_stage(timeline, logger)
    await sync_servers_stage(timeline, logger)
    await initialize_payment_methods_stage(timeline, logger)
    await load_bot_configuration_stage(timeline, logger)

    bot, dp = await setup_bot_stage(timeline)
    wire_core_services(bot, telegram_notifier)
    await connect_integration_services_stage(timeline, bot)

    await initialize_backup_stage(timeline, logger, bot)
    await initialize_reporting_stage(timeline, logger, bot)
    await initialize_referral_contests_stage(timeline, logger)
    await initialize_contest_rotation_stage(timeline, logger, bot)
    if settings.is_log_rotation_enabled():
        await initialize_log_rotation_stage(timeline, logger, bot)

    await initialize_remnawave_sync_stage(timeline, logger)

    payment_service = setup_payment_runtime(bot)
    verification_providers, auto_verification_active = await initialize_payment_verification_stage(timeline)
    await start_nalogo_queue_stage(timeline, logger, payment_service)
    await initialize_external_admin_stage(timeline, logger, bot)

    polling_enabled, telegram_webhook_enabled, payment_webhooks_enabled = resolve_runtime_mode()
    _web_app, web_api_server = await start_web_server_stage(
        timeline,
        bot,
        dp,
        payment_service,
        telegram_webhook_enabled=telegram_webhook_enabled,
        payment_webhooks_enabled=payment_webhooks_enabled,
    )
    await configure_telegram_webhook_stage(
        timeline,
        bot,
        dp,
        telegram_webhook_enabled=telegram_webhook_enabled,
    )

    return CoreRuntimeStartupContext(
        bot=bot,
        dp=dp,
        payment_service=payment_service,
        verification_providers=verification_providers,
        auto_verification_active=auto_verification_active,
        polling_enabled=polling_enabled,
        telegram_webhook_enabled=telegram_webhook_enabled,
        web_api_server=web_api_server,
    )
