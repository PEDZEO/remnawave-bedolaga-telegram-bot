from typing import Any

from app.config import settings
from app.database.models import Transaction

from ..schemas.miniapp import MiniAppTransaction


def resolve_display_name(user_data: dict[str, Any]) -> str:
    username = user_data.get('username')
    if username:
        return username

    first = user_data.get('first_name')
    last = user_data.get('last_name')
    parts = [part for part in [first, last] if part]
    if parts:
        return ' '.join(parts)

    telegram_id = user_data.get('telegram_id')
    return f'User {telegram_id}' if telegram_id else 'User'


def is_remnawave_configured() -> bool:
    params = settings.get_remnawave_auth_params()
    return bool(params.get('base_url') and params.get('api_key'))


def serialize_transaction(transaction: Transaction) -> MiniAppTransaction:
    return MiniAppTransaction(
        id=transaction.id,
        type=transaction.type,
        amount_kopeks=transaction.amount_kopeks,
        amount_rubles=round(transaction.amount_kopeks / 100, 2),
        description=transaction.description,
        payment_method=transaction.payment_method,
        external_id=transaction.external_id,
        is_completed=transaction.is_completed,
        created_at=transaction.created_at,
        completed_at=transaction.completed_at,
    )
