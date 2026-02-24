_PAYMENT_SUCCESS_STATUSES = {
    'success',
    'paid',
    'confirmed',
    'completed',
    'succeeded',
    'finished',
}

_PAYMENT_FAILURE_STATUSES = {
    'failed',
    'error',
    'cancelled',
    'canceled',
    'expired',
    'rejected',
}


def classify_payment_status(status: str | None, is_paid: bool) -> str:
    if is_paid:
        return 'paid'
    normalized = (status or '').strip().lower()
    if not normalized:
        return 'pending'
    if normalized in _PAYMENT_SUCCESS_STATUSES:
        return 'paid'
    if normalized in _PAYMENT_FAILURE_STATUSES:
        return 'failed'
    return 'pending'
