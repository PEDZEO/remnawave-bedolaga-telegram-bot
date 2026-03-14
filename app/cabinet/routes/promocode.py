"""Promo code routes for cabinet."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import GuestPurchase, GuestPurchaseStatus, User
from app.services.guest_purchase_service import GuestPurchaseError, activate_purchase as activate_gift_purchase
from app.services.promocode_service import PromoCodeService

from ..dependencies import get_cabinet_db, get_current_cabinet_user


logger = structlog.get_logger(__name__)

router = APIRouter(prefix='/promocode', tags=['Cabinet Promocode'])


class PromocodeActivateRequest(BaseModel):
    """Request to activate a promo code."""

    code: str = Field(..., min_length=1, max_length=50, description='Promo code to activate')


class PromocodeActivateResponse(BaseModel):
    """Response after activating a promo code."""

    success: bool
    message: str
    balance_before: float = 0
    balance_after: float = 0
    bonus_description: str | None = None
    activated_gift: bool = False
    gift_tariff_name: str | None = None
    gift_period_days: int | None = None


class PromocodeDeactivateResponse(BaseModel):
    """Response after deactivating a discount promo code."""

    success: bool
    message: str
    deactivated_code: str | None = None
    discount_percent: int = 0


@router.post('/activate', response_model=PromocodeActivateResponse)
async def activate_promocode(
    request: PromocodeActivateRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    """Activate a promo code for the current user."""
    raw_code = request.code.strip()
    normalized_code = raw_code
    if normalized_code.upper().startswith('GIFT-'):
        normalized_code = normalized_code[5:]

    # Ultima flow: allow activating gift-code directly via promocode input.
    # We require explicit GIFT- prefix to avoid collisions with regular promo codes.
    if raw_code.upper().startswith('GIFT-'):
        if len(normalized_code) < 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Code too short')

        token_filter = (
            GuestPurchase.token == normalized_code
            if len(normalized_code) >= 64
            else GuestPurchase.token.startswith(normalized_code)
        )
        gift_query = await db.execute(
            select(GuestPurchase)
            .options(selectinload(GuestPurchase.tariff))
            .where(token_filter, GuestPurchase.is_gift.is_(True))
            .with_for_update()
        )
        purchase = gift_query.scalars().first()
        if purchase is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Gift not found')
        if purchase.buyer_user_id is not None and purchase.buyer_user_id == user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot activate your own gift')

        if purchase.status == GuestPurchaseStatus.DELIVERED.value:
            return PromocodeActivateResponse(
                success=True,
                message='Gift already activated',
                bonus_description='Gift activated successfully',
                activated_gift=True,
                gift_tariff_name=purchase.tariff.name if purchase.tariff else None,
                gift_period_days=purchase.period_days,
            )

        activatable = {GuestPurchaseStatus.PENDING_ACTIVATION.value, GuestPurchaseStatus.PAID.value}
        if purchase.status not in activatable:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='This gift cannot be activated')

        if purchase.user_id is None:
            purchase.user_id = user.id
        elif purchase.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Gift not found')

        if purchase.status == GuestPurchaseStatus.PAID.value:
            purchase.status = GuestPurchaseStatus.PENDING_ACTIVATION.value
        await db.flush()

        try:
            await activate_gift_purchase(db, purchase.token, skip_notification=True)
        except GuestPurchaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        return PromocodeActivateResponse(
            success=True,
            message='Gift activated successfully',
            bonus_description='Gift activated successfully',
            activated_gift=True,
            gift_tariff_name=purchase.tariff.name if purchase.tariff else None,
            gift_period_days=purchase.period_days,
        )

    promocode_service = PromoCodeService()

    result = await promocode_service.activate_promocode(db=db, user_id=user.id, code=normalized_code)

    if result['success']:
        balance_before_rubles = result.get('balance_before_kopeks', 0) / 100
        balance_after_rubles = result.get('balance_after_kopeks', 0) / 100

        return PromocodeActivateResponse(
            success=True,
            message='Promo code activated successfully',
            balance_before=balance_before_rubles,
            balance_after=balance_after_rubles,
            bonus_description=result.get('description'),
        )

    # Map error codes to messages
    error_messages = {
        'not_found': 'Promo code not found',
        'expired': 'Promo code has expired',
        'used': 'Promo code has been fully used',
        'already_used_by_user': 'You have already used this promo code',
        'active_discount_exists': 'You already have an active discount. Deactivate it first via /deactivate-discount',
        'no_subscription_for_days': 'This promo code requires an active or expired subscription',
        'not_first_purchase': 'This promo code is only available for first purchase',
        'daily_limit': 'Too many promo code activations today',
        'user_not_found': 'User not found',
        'server_error': 'Server error occurred',
    }

    error_code = result.get('error', 'server_error')
    error_message = error_messages.get(error_code, 'Failed to activate promo code')

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_message,
    )


@router.post('/deactivate-discount', response_model=PromocodeDeactivateResponse)
async def deactivate_discount_promocode(
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
) -> PromocodeDeactivateResponse:
    """Deactivate the currently active discount promo code for the current user."""
    promocode_service = PromoCodeService()

    result = await promocode_service.deactivate_discount_promocode(
        db=db,
        user_id=user.id,
        admin_initiated=False,
    )

    if result['success']:
        return PromocodeDeactivateResponse(
            success=True,
            message='Discount promo code deactivated successfully',
            deactivated_code=result.get('deactivated_code'),
            discount_percent=result.get('discount_percent', 0),
        )

    error_messages = {
        'user_not_found': 'User not found',
        'no_active_discount_promocode': 'No active discount promo code found',
        'discount_already_expired': 'Discount has already expired',
        'server_error': 'Server error occurred',
    }

    error_code = result.get('error', 'server_error')
    error_message = error_messages.get(error_code, 'Failed to deactivate promo code')

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_message,
    )
