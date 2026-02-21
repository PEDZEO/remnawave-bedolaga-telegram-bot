from typing import Any

from aiogram import Bot, Dispatcher

from app.config import settings
from app.services.payment_service import PaymentService
from app.utils.startup_timeline import StartupTimeline
from app.webapi.server import WebAPIServer
from app.webserver.unified_app import create_unified_app


async def start_web_server_stage(
    timeline: StartupTimeline,
    bot: Bot,
    dp: Dispatcher,
    payment_service: PaymentService,
    telegram_webhook_enabled: bool,
    payment_webhooks_enabled: bool,
) -> tuple[Any, WebAPIServer | None]:
    web_app = None
    web_api_server = None

    async with timeline.stage(
        'Единый веб-сервер',
        '🌐',
        success_message='Веб-сервер запущен',
    ) as stage:
        should_start_web_app = (
            settings.is_web_api_enabled()
            or telegram_webhook_enabled
            or payment_webhooks_enabled
            or settings.get_miniapp_static_path().exists()
        )

        if should_start_web_app:
            web_app = create_unified_app(
                bot,
                dp,
                payment_service,
                enable_telegram_webhook=telegram_webhook_enabled,
            )

            web_api_server = WebAPIServer(app=web_app)
            await web_api_server.start()

            base_url = settings.WEBHOOK_URL or f'http://{settings.WEB_API_HOST}:{settings.WEB_API_PORT}'
            stage.log(f'Базовый URL: {base_url}')

            features: list[str] = []
            if settings.is_web_api_enabled():
                features.append('админка')
            if payment_webhooks_enabled:
                features.append('платежные webhook-и')
            if telegram_webhook_enabled:
                features.append('Telegram webhook')
            if settings.get_miniapp_static_path().exists():
                features.append('статические файлы миниаппа')

            if features:
                stage.log('Активные сервисы: ' + ', '.join(features))
            stage.success('HTTP-сервисы активны')
        else:
            stage.skip('HTTP-сервисы отключены настройками')

    return web_app, web_api_server
