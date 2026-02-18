"""Helpers for manual merge support-ticket metadata."""

from __future__ import annotations

import re
from datetime import UTC, datetime


MANUAL_MERGE_TICKET_TITLE = 'Manual account merge request'
MANUAL_MERGE_MARKER = '[MANUAL_MERGE_V1]'
MANUAL_MERGE_RESOLUTION_MARKER = '[MANUAL_MERGE_RESOLUTION_V1]'


def _format_identity_hints(hints: dict[str, str]) -> str:
    if not hints:
        return 'нет данных'
    return ', '.join(f'{provider}: {masked_id}' for provider, masked_id in sorted(hints.items()))


def build_manual_merge_ticket_message(
    *,
    current_user_id: int,
    source_user_id: int,
    current_user_hints: dict[str, str],
    source_user_hints: dict[str, str],
    comment: str | None = None,
) -> str:
    """Build support ticket message in a human-readable Russian format."""
    lines = [
        'Запрос на ручное объединение аккаунтов.',
        f'Создано: {datetime.now(UTC).isoformat()}',
        f'ID текущего аккаунта: {current_user_id}',
        f'ID аккаунта по коду: {source_user_id}',
        f'Привязки текущего аккаунта: {_format_identity_hints(current_user_hints)}',
        f'Привязки аккаунта по коду: {_format_identity_hints(source_user_hints)}',
    ]
    if comment:
        lines.append(f'Комментарий пользователя: {comment}')
    return '\n'.join(lines)


def parse_manual_merge_payload(message_text: str) -> dict[str, int] | None:
    """Extract user ids from manual merge ticket message."""
    if not message_text:
        return None

    current_match = re.search(r'(?m)^current_user_id=(\d+)$', message_text)
    source_match = re.search(r'(?m)^source_user_id=(\d+)$', message_text)

    # Backward compatibility for old ticket format.
    if not current_match:
        current_match = re.search(r'Current user id:\s*(\d+)', message_text)
    if not source_match:
        source_match = re.search(r'Code source user id:\s*(\d+)', message_text)
    # New readable format.
    if not current_match:
        current_match = re.search(r'ID текущего аккаунта:\s*(\d+)', message_text)
    if not source_match:
        source_match = re.search(r'ID аккаунта по коду:\s*(\d+)', message_text)

    if not current_match or not source_match:
        return None

    return {
        'current_user_id': int(current_match.group(1)),
        'source_user_id': int(source_match.group(1)),
    }


def build_manual_merge_resolution_message(
    *,
    action: str,
    admin_user_id: int,
    primary_user_id: int | None,
    secondary_user_id: int | None,
    comment: str | None = None,
) -> str:
    """Build admin resolution message in a human-readable Russian format."""
    action_label = 'Одобрено' if action == 'approve' else 'Отклонено'
    lines = [
        f'Решение по ручному объединению: {action_label}',
        f'ID администратора: {admin_user_id}',
        f'Время решения: {datetime.now(UTC).isoformat()}',
    ]
    if primary_user_id is not None:
        lines.append(f'Основной аккаунт после решения: ID {primary_user_id}')
    if secondary_user_id is not None:
        lines.append(f'Второй аккаунт: ID {secondary_user_id}')
    if comment:
        lines.append(f'Комментарий администратора: {comment}')
    return '\n'.join(lines)


def parse_manual_merge_resolution(message_text: str) -> dict[str, str | int] | None:
    """Parse approval/rejection from old and new admin resolution formats."""
    text = message_text or ''
    action_match = re.search(r'(?m)^action=(approve|reject)$', text)
    if not action_match:
        action_label_match = re.search(r'Решение по ручному объединению:\s*(Одобрено|Отклонено)', text)
        if action_label_match:
            action_value = 'approve' if action_label_match.group(1) == 'Одобрено' else 'reject'
            action_match = re.search(rf'({action_value})', action_value)

    admin_match = re.search(r'(?m)^admin_user_id=(\d+)$', text) or re.search(
        r'ID администратора:\s*(\d+)',
        text,
    )
    primary_match = re.search(r'(?m)^primary_user_id=(\d+)$', text) or re.search(
        r'Основной аккаунт после решения:\s*ID\s*(\d+)',
        text,
    )
    secondary_match = re.search(r'(?m)^secondary_user_id=(\d+)$', text) or re.search(
        r'Второй аккаунт:\s*ID\s*(\d+)',
        text,
    )
    comment_match = re.search(r'(?m)^comment=(.+)$', text) or re.search(
        r'Комментарий администратора:\s*(.+)',
        text,
    )

    if not action_match:
        return None

    parsed: dict[str, str | int] = {'action': action_match.group(1)}
    if admin_match:
        parsed['admin_user_id'] = int(admin_match.group(1))
    if primary_match:
        parsed['primary_user_id'] = int(primary_match.group(1))
    if secondary_match:
        parsed['secondary_user_id'] = int(secondary_match.group(1))
    if comment_match:
        parsed['comment'] = comment_match.group(1).strip()
    return parsed
