"""Helpers for manual merge support-ticket metadata."""

from __future__ import annotations

from datetime import UTC, datetime
import re


MANUAL_MERGE_TICKET_TITLE = 'Manual account merge request'
MANUAL_MERGE_MARKER = '[MANUAL_MERGE_V1]'
MANUAL_MERGE_RESOLUTION_MARKER = '[MANUAL_MERGE_RESOLUTION_V1]'


def build_manual_merge_ticket_message(
    *,
    current_user_id: int,
    source_user_id: int,
    current_user_hints: dict[str, str],
    source_user_hints: dict[str, str],
    comment: str | None = None,
) -> str:
    """Build support ticket message with machine-readable metadata."""
    lines = [
        MANUAL_MERGE_MARKER,
        f'current_user_id={current_user_id}',
        f'source_user_id={source_user_id}',
        f'created_at={datetime.now(UTC).isoformat()}',
        '',
        'User requested manual merge for disputed account-linking case.',
        f'Current user identities: {current_user_hints}',
        f'Source user identities: {source_user_hints}',
    ]
    if comment:
        lines.append(f'User comment: {comment}')
    return '\n'.join(lines)


def parse_manual_merge_payload(message_text: str) -> dict[str, int] | None:
    """Extract user ids from manual merge ticket message."""
    if not message_text:
        return None

    current_match = re.search(r'current_user_id=(\d+)', message_text)
    source_match = re.search(r'source_user_id=(\d+)', message_text)

    # Backward compatibility for old ticket format.
    if not current_match:
        current_match = re.search(r'Current user id:\s*(\d+)', message_text)
    if not source_match:
        source_match = re.search(r'Code source user id:\s*(\d+)', message_text)

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
    """Build machine-readable admin resolution message."""
    lines = [
        MANUAL_MERGE_RESOLUTION_MARKER,
        f'action={action}',
        f'admin_user_id={admin_user_id}',
        f'resolved_at={datetime.now(UTC).isoformat()}',
    ]
    if primary_user_id is not None:
        lines.append(f'primary_user_id={primary_user_id}')
    if secondary_user_id is not None:
        lines.append(f'secondary_user_id={secondary_user_id}')
    if comment:
        lines.append(f'comment={comment}')
    return '\n'.join(lines)


def parse_manual_merge_resolution(message_text: str) -> dict[str, str | int] | None:
    """Parse approval/rejection from admin message marker."""
    if MANUAL_MERGE_RESOLUTION_MARKER not in (message_text or ''):
        return None

    action_match = re.search(r'action=(approve|reject)', message_text)
    admin_match = re.search(r'admin_user_id=(\d+)', message_text)
    primary_match = re.search(r'primary_user_id=(\d+)', message_text)
    secondary_match = re.search(r'secondary_user_id=(\d+)', message_text)
    comment_match = re.search(r'comment=(.+)', message_text)

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

