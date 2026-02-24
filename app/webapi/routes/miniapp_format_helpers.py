def format_gb(value: float | None) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def format_gb_label(value: float) -> str:
    absolute = abs(value)
    if absolute >= 100:
        return f'{value:.0f} GB'
    if absolute >= 10:
        return f'{value:.1f} GB'
    return f'{value:.2f} GB'


def format_limit_label(limit: int | None) -> str:
    if not limit:
        return 'Unlimited'
    return f'{limit} GB'


def bytes_to_gb(bytes_value: int | None) -> float:
    if not bytes_value:
        return 0.0
    return round(bytes_value / (1024**3), 2)


def status_label(status: str) -> str:
    mapping = {
        'active': 'Active',
        'trial': 'Trial',
        'expired': 'Expired',
        'disabled': 'Disabled',
    }
    return mapping.get(status, status.title())


def format_payment_method_title(method: str) -> str:
    mapping = {
        'cryptobot': 'CryptoBot',
        'yookassa': 'YooKassa',
        'yookassa_sbp': 'YooKassa СБП',
        'mulenpay': 'MulenPay',
        'pal24': 'Pal24',
        'wata': 'WataPay',
        'heleket': 'Heleket',
        'tribute': 'Tribute',
        'stars': 'Telegram Stars',
    }
    key = (method or '').lower()
    return mapping.get(key, method.title() if method else '')


def format_traffic_limit_label(traffic_gb: int) -> str:
    if traffic_gb == 0:
        return '♾️ Безлимит'
    return f'{traffic_gb} ГБ'
