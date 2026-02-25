import pytest

from app.external.remnawave_api import RemnaWaveAPI, UserStatus


@pytest.mark.parametrize(
    ('raw_status', 'expected'),
    [
        (UserStatus.ACTIVE, UserStatus.ACTIVE),
        (UserStatus.DISABLED, UserStatus.DISABLED),
        (UserStatus.EXPIRED, UserStatus.DISABLED),
        (UserStatus.LIMITED, UserStatus.DISABLED),
        ('ACTIVE', UserStatus.ACTIVE),
        ('expired', UserStatus.DISABLED),
        ('limited', UserStatus.DISABLED),
        ('unknown', UserStatus.DISABLED),
    ],
)
def test_normalize_mutable_user_status(raw_status: UserStatus | str, expected: UserStatus):
    result = RemnaWaveAPI._normalize_mutable_user_status(raw_status)
    assert result is expected


def test_normalize_mutable_user_status_none_for_update():
    result = RemnaWaveAPI._normalize_mutable_user_status(None, allow_none=True)
    assert result is None
