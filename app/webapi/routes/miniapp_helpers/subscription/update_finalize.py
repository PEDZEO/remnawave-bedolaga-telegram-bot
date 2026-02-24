from __future__ import annotations

from datetime import UTC, datetime


async def finalize_subscription_update(
    db,
    user,
    subscription,
    *,
    change_type: str,
    old_value,
    new_value,
    price_paid: int,
    with_admin_notification_service,
) -> None:
    from app.services.subscription_service import SubscriptionService

    subscription.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(subscription)
    try:
        await db.refresh(user)
    except Exception:
        pass

    service = SubscriptionService()
    await service.update_remnawave_user(db, subscription)

    await with_admin_notification_service(
        lambda service: service.send_subscription_update_notification(
            db,
            user,
            subscription,
            change_type,
            old_value,
            new_value,
            price_paid=price_paid,
        )
    )
