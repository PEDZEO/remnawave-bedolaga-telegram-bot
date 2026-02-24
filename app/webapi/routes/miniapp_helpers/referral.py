from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import User
from app.utils.user_utils import (
    get_detailed_referral_list,
    get_effective_referral_commission_percent,
    get_user_referral_summary,
)

from ...schemas.miniapp import (
    MiniAppReferralInfo,
    MiniAppReferralItem,
    MiniAppReferralList,
    MiniAppReferralRecentEarning,
    MiniAppReferralStats,
    MiniAppReferralTerms,
)


async def build_referral_info(
    db: AsyncSession,
    user: User,
) -> MiniAppReferralInfo | None:
    referral_code = getattr(user, 'referral_code', None)
    referral_settings = settings.get_referral_settings() or {}

    bot_username = settings.get_bot_username()
    referral_link = None
    if referral_code and bot_username:
        referral_link = f'https://t.me/{bot_username}?start={referral_code}'

    minimum_topup_kopeks = int(referral_settings.get('minimum_topup_kopeks') or 0)
    first_topup_bonus_kopeks = int(referral_settings.get('first_topup_bonus_kopeks') or 0)
    inviter_bonus_kopeks = int(referral_settings.get('inviter_bonus_kopeks') or 0)
    commission_percent = float(
        get_effective_referral_commission_percent(user) if user else referral_settings.get('commission_percent') or 0
    )

    terms = MiniAppReferralTerms(
        minimum_topup_kopeks=minimum_topup_kopeks,
        minimum_topup_label=settings.format_price(minimum_topup_kopeks),
        first_topup_bonus_kopeks=first_topup_bonus_kopeks,
        first_topup_bonus_label=settings.format_price(first_topup_bonus_kopeks),
        inviter_bonus_kopeks=inviter_bonus_kopeks,
        inviter_bonus_label=settings.format_price(inviter_bonus_kopeks),
        commission_percent=commission_percent,
    )

    summary = await get_user_referral_summary(db, user.id)
    stats: MiniAppReferralStats | None = None
    recent_earnings: list[MiniAppReferralRecentEarning] = []

    if summary:
        total_earned_kopeks = int(summary.get('total_earned_kopeks') or 0)
        month_earned_kopeks = int(summary.get('month_earned_kopeks') or 0)

        stats = MiniAppReferralStats(
            invited_count=int(summary.get('invited_count') or 0),
            paid_referrals_count=int(summary.get('paid_referrals_count') or 0),
            active_referrals_count=int(summary.get('active_referrals_count') or 0),
            total_earned_kopeks=total_earned_kopeks,
            total_earned_label=settings.format_price(total_earned_kopeks),
            month_earned_kopeks=month_earned_kopeks,
            month_earned_label=settings.format_price(month_earned_kopeks),
            conversion_rate=float(summary.get('conversion_rate') or 0.0),
        )

        for earning in summary.get('recent_earnings', []) or []:
            amount = int(earning.get('amount_kopeks') or 0)
            recent_earnings.append(
                MiniAppReferralRecentEarning(
                    amount_kopeks=amount,
                    amount_label=settings.format_price(amount),
                    reason=earning.get('reason'),
                    referral_name=earning.get('referral_name'),
                    created_at=earning.get('created_at'),
                )
            )

    detailed = await get_detailed_referral_list(db, user.id, limit=50, offset=0)
    referral_items: list[MiniAppReferralItem] = []
    if detailed:
        for item in detailed.get('referrals', []) or []:
            total_earned = int(item.get('total_earned_kopeks') or 0)
            balance = int(item.get('balance_kopeks') or 0)
            referral_items.append(
                MiniAppReferralItem(
                    id=int(item.get('id') or 0),
                    telegram_id=item.get('telegram_id'),
                    full_name=item.get('full_name'),
                    username=item.get('username'),
                    created_at=item.get('created_at'),
                    last_activity=item.get('last_activity'),
                    has_made_first_topup=bool(item.get('has_made_first_topup')),
                    balance_kopeks=balance,
                    balance_label=settings.format_price(balance),
                    total_earned_kopeks=total_earned,
                    total_earned_label=settings.format_price(total_earned),
                    topups_count=int(item.get('topups_count') or 0),
                    days_since_registration=item.get('days_since_registration'),
                    days_since_activity=item.get('days_since_activity'),
                    status=item.get('status'),
                )
            )

    referral_list = MiniAppReferralList(
        total_count=int(detailed.get('total_count') or 0) if detailed else 0,
        has_next=bool(detailed.get('has_next')) if detailed else False,
        has_prev=bool(detailed.get('has_prev')) if detailed else False,
        current_page=int(detailed.get('current_page') or 1) if detailed else 1,
        total_pages=int(detailed.get('total_pages') or 1) if detailed else 1,
        items=referral_items,
    )

    if (
        not referral_code
        and not referral_link
        and not referral_items
        and not recent_earnings
        and (not stats or (stats.invited_count == 0 and stats.total_earned_kopeks == 0))
    ):
        return None

    return MiniAppReferralInfo(
        referral_code=referral_code,
        referral_link=referral_link,
        terms=terms,
        stats=stats,
        recent_earnings=recent_earnings,
        referrals=referral_list,
    )
