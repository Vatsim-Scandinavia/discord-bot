from types import SimpleNamespace

import pytest

from helpers.handler import Handler


@pytest.mark.parametrize(
    ('nick', 'expected_cid'),
    [
        ('John Doe - 1234567', 1234567),
        ('John Doe - 1234567   ', 1234567),
        ('John Doe - 800000', 800000),
        ('SAS123 | John Doe - 1234567', 1234567),
        ('SAS123 | |-1234567-|', 1234567),
        ('ESOS 1 CTR | John Doe - 1234567', 1234567),
        ('ESOS 1 CTR | |-1234567-|', 1234567),
        ('EKCH DEL | John Doe - 1234567', 1234567),
        ('AB1_CD2 | John Doe - 1234567', 1234567),
        ('SAS123 | John Doe 2024 1234567', 1234567),
        ('SAS123 | John Doe 799999 1234567', 1234567),
        ('John Doe 2024 1234567', 1234567),
    ],
)
def test_get_cid_returns_expected_suffix_cid(nick: str, expected_cid: int) -> None:
    member = SimpleNamespace(nick=nick)

    assert Handler().get_cid(member) == expected_cid


@pytest.mark.parametrize(
    'nick',
    [
        None,
        '',
        'John Doe',
        'No CID here either',
        'John Doe - 799999',
        'SAS123 | |-799999-|',
        'John Doe 2024 799999',
    ],
)
def test_get_cid_raises_value_error_for_missing_cid(nick: str | None) -> None:
    member = SimpleNamespace(nick=nick)

    with pytest.raises(ValueError, match=r'^$'):
        Handler().get_cid(member)
