from fastapi import HTTPException, status

from app.config import settings


def get_tariff_monthly_price(tariff) -> int:
    """Получает месячную цену тарифа (30 дней) с fallback на пропорциональный расчёт."""
    price = tariff.get_price_for_period(30)
    if price is not None:
        return price

    periods = tariff.get_available_periods()
    if periods:
        first_period = periods[0]
        first_price = tariff.get_price_for_period(first_period)
        if first_price:
            return int(first_price * 30 / first_period)

    return 0


def ensure_tariffs_mode_enabled(*, message: str = 'Tariffs mode is not enabled') -> None:
    if settings.is_tariffs_mode():
        return

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            'code': 'tariffs_mode_disabled',
            'message': message,
        },
    )
