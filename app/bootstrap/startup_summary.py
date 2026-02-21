import asyncio

from app.config import settings
from app.services.payment_verification_service import auto_payment_verification_service
from app.services.reporting_service import reporting_service
from app.utils.startup_timeline import StartupTimeline


def log_startup_summary(
    timeline: StartupTimeline,
    *,
    telegram_webhook_enabled: bool,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    verification_providers: list[str],
) -> None:
    webhook_lines: list[str] = []
    base_url = settings.WEBHOOK_URL or f'http://{settings.WEB_API_HOST}:{settings.WEB_API_PORT}'

    def _fmt(path: str) -> str:
        return f'{base_url}{path if path.startswith("/") else "/" + path}'

    telegram_webhook_url = settings.get_telegram_webhook_url()
    if telegram_webhook_enabled and telegram_webhook_url:
        webhook_lines.append(f'Telegram: {telegram_webhook_url}')
    if settings.TRIBUTE_ENABLED:
        webhook_lines.append(f'Tribute: {_fmt(settings.TRIBUTE_WEBHOOK_PATH)}')
    if settings.is_mulenpay_enabled():
        webhook_lines.append(f'{settings.get_mulenpay_display_name()}: {_fmt(settings.MULENPAY_WEBHOOK_PATH)}')
    if settings.is_cryptobot_enabled():
        webhook_lines.append(f'CryptoBot: {_fmt(settings.CRYPTOBOT_WEBHOOK_PATH)}')
    if settings.is_yookassa_enabled():
        webhook_lines.append(f'YooKassa: {_fmt(settings.YOOKASSA_WEBHOOK_PATH)}')
    if settings.is_pal24_enabled():
        webhook_lines.append(f'PayPalych: {_fmt(settings.PAL24_WEBHOOK_PATH)}')
    if settings.is_wata_enabled():
        webhook_lines.append(f'WATA: {_fmt(settings.WATA_WEBHOOK_PATH)}')
    if settings.is_heleket_enabled():
        webhook_lines.append(f'Heleket: {_fmt(settings.HELEKET_WEBHOOK_PATH)}')
    if settings.is_platega_enabled():
        webhook_lines.append(f'Platega: {_fmt(settings.PLATEGA_WEBHOOK_PATH)}')
    if settings.is_cloudpayments_enabled():
        webhook_lines.append(f'CloudPayments: {_fmt(settings.CLOUDPAYMENTS_WEBHOOK_PATH)}')
    if settings.is_freekassa_enabled():
        webhook_lines.append(f'Freekassa: {_fmt(settings.FREEKASSA_WEBHOOK_PATH)}')
    if settings.is_kassa_ai_enabled():
        webhook_lines.append(f'Kassa.ai: {_fmt(settings.KASSA_AI_WEBHOOK_PATH)}')
    if settings.is_remnawave_webhook_enabled():
        webhook_lines.append(f'RemnaWave: {_fmt(settings.REMNAWAVE_WEBHOOK_PATH)}')

    timeline.log_section(
        'Активные webhook endpoints',
        webhook_lines or ['Нет активных endpoints'],
        icon='🎯',
    )

    services_lines = [
        f'Мониторинг: {"Включен" if monitoring_task else "Отключен"}',
        f'Техработы: {"Включен" if maintenance_task else "Отключен"}',
        f'Мониторинг трафика: {"Включен" if traffic_monitoring_task else "Отключен"}',
        f'Суточные подписки: {"Включен" if daily_subscription_task else "Отключен"}',
        f'Проверка версий: {"Включен" if version_check_task else "Отключен"}',
        f'Отчеты: {"Включен" if reporting_service.is_running() else "Отключен"}',
    ]
    services_lines.append('Проверка пополнений: ' + ('Включена' if verification_providers else 'Отключена'))
    services_lines.append(
        'Автопроверка пополнений: '
        + ('Включена' if auto_payment_verification_service.is_running() else 'Отключена')
    )
    timeline.log_section('Активные фоновые сервисы', services_lines, icon='📄')

    timeline.log_summary()
