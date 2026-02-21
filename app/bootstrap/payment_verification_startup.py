from app.config import settings
from app.database.models import PaymentMethod
from app.services.payment_verification_service import (
    PENDING_MAX_AGE,
    SUPPORTED_MANUAL_CHECK_METHODS,
    auto_payment_verification_service,
    get_enabled_auto_methods,
    method_display_name,
)
from app.utils.startup_timeline import StartupTimeline


async def initialize_payment_verification_stage(timeline: StartupTimeline) -> tuple[list[str], bool]:
    verification_providers: list[str] = []
    auto_verification_active = False

    async with timeline.stage(
        'Сервис проверки пополнений',
        '💳',
        success_message='Ручная проверка активна',
    ) as stage:
        for method in SUPPORTED_MANUAL_CHECK_METHODS:
            if method == PaymentMethod.YOOKASSA and settings.is_yookassa_enabled():
                verification_providers.append('YooKassa')
            elif method == PaymentMethod.MULENPAY and settings.is_mulenpay_enabled():
                verification_providers.append(settings.get_mulenpay_display_name())
            elif method == PaymentMethod.PAL24 and settings.is_pal24_enabled():
                verification_providers.append('PayPalych')
            elif method == PaymentMethod.WATA and settings.is_wata_enabled():
                verification_providers.append('WATA')
            elif method == PaymentMethod.HELEKET and settings.is_heleket_enabled():
                verification_providers.append('Heleket')
            elif method == PaymentMethod.CRYPTOBOT and settings.is_cryptobot_enabled():
                verification_providers.append('CryptoBot')

        if verification_providers:
            hours = int(PENDING_MAX_AGE.total_seconds() // 3600)
            stage.log(f'Ожидающие пополнения автоматически отбираются не старше {hours}ч')
            stage.log('Доступна ручная проверка для: ' + ', '.join(sorted(verification_providers)))
            stage.success(f'Активно провайдеров: {len(verification_providers)}')
        else:
            stage.skip('Нет активных провайдеров для ручной проверки')

        if settings.is_payment_verification_auto_check_enabled():
            auto_methods = get_enabled_auto_methods()
            if auto_methods:
                interval_minutes = settings.get_payment_verification_auto_check_interval()
                auto_labels = ', '.join(sorted(method_display_name(method) for method in auto_methods))
                stage.log(f'Автопроверка каждые {interval_minutes} мин: {auto_labels}')
            else:
                stage.log('Автопроверка включена, но нет активных провайдеров')
        else:
            stage.log('Автопроверка отключена настройками')

        await auto_payment_verification_service.start()
        auto_verification_active = auto_payment_verification_service.is_running()
        if auto_verification_active:
            stage.log('Фоновая автопроверка запущена')

    return verification_providers, auto_verification_active
