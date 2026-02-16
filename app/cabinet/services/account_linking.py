"""Account linking service for secure provider sync across user accounts."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import Subscription, Transaction, User, UserStatus
from app.utils.cache import cache, cache_key


logger = structlog.get_logger(__name__)

LINK_CODE_TTL_SECONDS = 10 * 60
LINK_CODE_MAX_ATTEMPTS = 5
LINK_CODE_LENGTH = 8
LINK_CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

_OAUTH_PROVIDER_COLUMNS: dict[str, str] = {
    'google': 'google_id',
    'yandex': 'yandex_id',
    'discord': 'discord_id',
    'vk': 'vk_id',
}


@dataclass(frozen=True)
class LinkCodePayload:
    source_user_id: int
    created_at: str


class LinkCodeError(ValueError):
    """Base link-code error."""


class LinkCodeInvalidError(LinkCodeError):
    """Code is invalid or expired."""


class LinkCodeAttemptsExceededError(LinkCodeError):
    """Too many attempts for this code."""


class LinkCodeConflictError(LinkCodeError):
    """Account linking conflict."""


def _now_naive_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _make_code() -> str:
    return ''.join(secrets.choice(LINK_CODE_ALPHABET) for _ in range(LINK_CODE_LENGTH))


def _hash_code(code: str) -> str:
    pepper = settings.get_cabinet_jwt_secret()
    digest = hashlib.sha256(f'{pepper}:{code.upper().strip()}'.encode()).hexdigest()
    return digest


def _code_key(code_hash: str) -> str:
    return cache_key('cabinet', 'link_code', code_hash)


def _source_pointer_key(source_user_id: int) -> str:
    return cache_key('cabinet', 'link_code', 'source', source_user_id)


def _attempts_key(code_hash: str, target_user_id: int) -> str:
    return cache_key('cabinet', 'link_code', 'attempts', code_hash, target_user_id)


def _mask_value(value: str, keep: int = 3) -> str:
    if len(value) <= keep:
        return value
    return f'{value[:keep]}***'


def get_user_identities(user: User) -> dict[str, str]:
    identities: dict[str, str] = {}
    if user.telegram_id is not None:
        identities['telegram'] = str(user.telegram_id)
    for provider, column_name in _OAUTH_PROVIDER_COLUMNS.items():
        value = getattr(user, column_name)
        if value is not None:
            identities[provider] = str(value)
    return identities


def get_user_identity_hints(user: User) -> dict[str, str]:
    hints: dict[str, str] = {}
    for provider, raw_value in get_user_identities(user).items():
        hints[provider] = _mask_value(raw_value)
    return hints


async def create_link_code(source_user: User) -> str:
    """Create one-time code bound to source account and persist in cache."""
    pointer_key = _source_pointer_key(source_user.id)
    old_code_hash = await cache.get(pointer_key)
    if isinstance(old_code_hash, str) and old_code_hash:
        await cache.delete(_code_key(old_code_hash))

    code = ''
    code_hash = ''
    saved = False
    for _ in range(5):
        candidate = _make_code()
        candidate_hash = _hash_code(candidate)
        payload = LinkCodePayload(
            source_user_id=source_user.id,
            created_at=_now_naive_utc().isoformat(),
        )
        saved = await cache.setnx(_code_key(candidate_hash), payload.__dict__, expire=LINK_CODE_TTL_SECONDS)
        if saved:
            code = candidate
            code_hash = candidate_hash
            break
    if not saved:
        raise LinkCodeError('Failed to allocate unique link code')
    await cache.set(pointer_key, code_hash, expire=LINK_CODE_TTL_SECONDS)

    logger.info('Account link code created', source_user_id=source_user.id)
    return code


async def _load_payload_by_code(code: str) -> tuple[LinkCodePayload, str]:
    code_hash = _hash_code(code)
    raw_payload = await cache.get(_code_key(code_hash))
    if not isinstance(raw_payload, dict):
        raise LinkCodeInvalidError('Code is invalid or expired')
    source_user_id = raw_payload.get('source_user_id')
    created_at = raw_payload.get('created_at')
    if not isinstance(source_user_id, int) or not isinstance(created_at, str):
        raise LinkCodeInvalidError('Code payload is invalid')
    return LinkCodePayload(source_user_id=source_user_id, created_at=created_at), code_hash


async def preview_link_code(code: str, target_user_id: int) -> int:
    """Validate code and return source user id for preview."""
    payload, _ = await _load_payload_by_code(code)

    if payload.source_user_id == target_user_id:
        raise LinkCodeConflictError('Cannot link account to itself')
    return payload.source_user_id


async def _check_confirm_attempts(code_hash: str, target_user_id: int) -> None:
    attempts_key = _attempts_key(code_hash, target_user_id)
    attempts = await cache.increment(attempts_key, 1)
    if attempts is None:
        raise LinkCodeError('Failed to validate attempts')
    if attempts == 1:
        await cache.expire(attempts_key, LINK_CODE_TTL_SECONDS)
    if attempts > LINK_CODE_MAX_ATTEMPTS:
        raise LinkCodeAttemptsExceededError('Too many code attempts')


async def _ensure_user_is_merge_safe(db: AsyncSession, user: User) -> None:
    """Allow auto-link only for clean secondary account to avoid unsafe data merges."""
    if user.balance_kopeks > 0:
        raise LinkCodeConflictError('Target account has non-zero balance')
    if user.remnawave_uuid:
        raise LinkCodeConflictError('Target account is already linked to remnawave profile')

    sub_result = await db.execute(select(Subscription.id).where(Subscription.user_id == user.id))
    if sub_result.scalar_one_or_none() is not None:
        raise LinkCodeConflictError('Target account has a subscription')

    tx_result = await db.execute(select(func.count(Transaction.id)).where(Transaction.user_id == user.id))
    transaction_count = int(tx_result.scalar() or 0)
    if transaction_count > 0:
        raise LinkCodeConflictError('Target account has transactions')


def _apply_identity_value(source_user: User, target_user: User, attr_name: str, label: str) -> None:
    source_value = getattr(source_user, attr_name)
    target_value = getattr(target_user, attr_name)
    if target_value is None:
        return
    if source_value is None:
        setattr(source_user, attr_name, target_value)
        setattr(target_user, attr_name, None)
        return
    if source_value != target_value:
        raise LinkCodeConflictError(f'Conflict for {label} identity')
    setattr(target_user, attr_name, None)


async def confirm_link_code(db: AsyncSession, code: str, target_user: User) -> User:
    """Move login identities from target user into source user."""
    payload, code_hash = await _load_payload_by_code(code)
    await _check_confirm_attempts(code_hash, target_user.id)

    stmt = select(User).where(User.id.in_([payload.source_user_id, target_user.id])).with_for_update()
    users_result = await db.execute(stmt)
    users = {user.id: user for user in users_result.scalars().all()}
    source_user = users.get(payload.source_user_id)
    locked_target_user = users.get(target_user.id)

    if source_user is None or locked_target_user is None:
        raise LinkCodeInvalidError('Source or target account not found')
    if source_user.id == locked_target_user.id:
        raise LinkCodeConflictError('Cannot link account to itself')
    if source_user.status != UserStatus.ACTIVE.value:
        raise LinkCodeConflictError('Source account is not active')
    if locked_target_user.status != UserStatus.ACTIVE.value:
        raise LinkCodeConflictError('Target account is not active')

    await _ensure_user_is_merge_safe(db, locked_target_user)

    had_target_telegram = locked_target_user.telegram_id is not None
    target_telegram_username = locked_target_user.username
    target_telegram_first_name = locked_target_user.first_name
    target_telegram_last_name = locked_target_user.last_name

    _apply_identity_value(source_user, locked_target_user, 'telegram_id', 'telegram')
    _apply_identity_value(source_user, locked_target_user, 'google_id', 'google')
    _apply_identity_value(source_user, locked_target_user, 'yandex_id', 'yandex')
    _apply_identity_value(source_user, locked_target_user, 'discord_id', 'discord')
    _apply_identity_value(source_user, locked_target_user, 'vk_id', 'vk')

    # If Telegram identity was linked, make profile canonical for Telegram login UX.
    if had_target_telegram and source_user.telegram_id is not None:
        if target_telegram_username:
            source_user.username = target_telegram_username
        if not source_user.first_name and target_telegram_first_name:
            source_user.first_name = target_telegram_first_name
        if not source_user.last_name and target_telegram_last_name:
            source_user.last_name = target_telegram_last_name
        source_user.auth_type = 'telegram'

    if source_user.email is None and locked_target_user.email and locked_target_user.email_verified:
        source_user.email = locked_target_user.email
        source_user.email_verified = True
        source_user.email_verified_at = locked_target_user.email_verified_at or _now_naive_utc()

    source_user.updated_at = _now_naive_utc()
    source_user.cabinet_last_login = _now_naive_utc()

    # Disable target account as standalone login profile.
    locked_target_user.auth_type = 'merged'
    locked_target_user.status = UserStatus.DELETED.value
    locked_target_user.email = None
    locked_target_user.email_verified = False
    locked_target_user.email_verified_at = None
    locked_target_user.password_hash = None
    locked_target_user.updated_at = _now_naive_utc()

    await db.commit()

    await cache.delete(_code_key(code_hash))
    await cache.delete(_source_pointer_key(source_user.id))
    await cache.delete(_attempts_key(code_hash, target_user.id))

    logger.info(
        'Account linking confirmed',
        source_user_id=source_user.id,
        target_user_id=target_user.id,
        source_identities=get_user_identity_hints(source_user),
    )
    return source_user
