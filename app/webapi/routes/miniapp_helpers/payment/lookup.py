from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PaymentMethod, Transaction, TransactionType


def parse_client_timestamp(value: str | float | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            timestamp = float(value)
        except (TypeError, ValueError):
            return None
        if timestamp > 1e12:
            timestamp /= 1000.0
        try:
            return datetime.fromtimestamp(timestamp, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.isdigit():
            return parse_client_timestamp(int(normalized))
        for suffix in ('Z', 'z'):
            if normalized.endswith(suffix):
                normalized = normalized[:-1] + '+00:00'
                break
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo:
            return parsed.astimezone(UTC)
        return parsed.replace(tzinfo=UTC)
    return None


async def find_recent_deposit(
    db: AsyncSession,
    *,
    user_id: int,
    payment_method: PaymentMethod,
    amount_kopeks: int | None,
    started_at: datetime | None,
    tolerance: timedelta = timedelta(minutes=5),
) -> Transaction | None:
    def _transaction_matches_started_at(
        transaction: Transaction,
        reference: datetime | None,
    ) -> bool:
        if not reference:
            return True
        timestamp = transaction.completed_at or transaction.created_at
        if not timestamp:
            return False
        if timestamp.tzinfo:
            timestamp = timestamp.astimezone(UTC)
        return timestamp >= reference

    query = (
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.DEPOSIT.value,
            Transaction.payment_method == payment_method.value,
        )
        .order_by(Transaction.created_at.desc())
        .limit(1)
    )

    if amount_kopeks is not None:
        query = query.where(Transaction.amount_kopeks == amount_kopeks)
    if started_at:
        query = query.where(Transaction.created_at >= started_at - tolerance)

    result = await db.execute(query)
    transaction = result.scalar_one_or_none()

    if not transaction:
        return None

    if not _transaction_matches_started_at(transaction, started_at):
        return None

    return transaction
