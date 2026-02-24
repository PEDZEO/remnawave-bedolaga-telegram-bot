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
