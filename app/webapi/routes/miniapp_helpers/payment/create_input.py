from __future__ import annotations

from fastapi import HTTPException, status

from .request import normalize_amount_kopeks


def resolve_create_payment_method(method: str | None) -> str:
    normalized = (method or '').strip().lower()
    if normalized:
        return normalized

    raise HTTPException(
        status.HTTP_400_BAD_REQUEST,
        detail='Payment method is required',
    )


def resolve_create_payment_amount(
    *,
    amount_rubles,
    amount_kopeks,
) -> int | None:
    return normalize_amount_kopeks(amount_rubles, amount_kopeks)
