from app.config import settings


def resolve_runtime_mode() -> tuple[bool, bool, bool]:
    bot_run_mode = settings.get_bot_run_mode()
    polling_enabled = bot_run_mode == 'polling'
    telegram_webhook_enabled = bot_run_mode == 'webhook'

    payment_webhooks_enabled = any(
        [
            settings.TRIBUTE_ENABLED,
            settings.is_cryptobot_enabled(),
            settings.is_mulenpay_enabled(),
            settings.is_yookassa_enabled(),
            settings.is_pal24_enabled(),
            settings.is_wata_enabled(),
            settings.is_heleket_enabled(),
        ]
    )

    return polling_enabled, telegram_webhook_enabled, payment_webhooks_enabled
