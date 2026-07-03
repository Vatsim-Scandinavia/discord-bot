import pytest

from cogs.roles import RolesCog


@pytest.fixture
def cog() -> RolesCog:
    # Bypass __init__ so we don't start the background task loop; get_mentor_roles
    # is a pure function of its arguments and needs no bot/loop state.
    return RolesCog.__new__(RolesCog)


CID = 1234567


@pytest.mark.parametrize(
    ('roles_payload', 'expect_mentor', 'expect_buddy', 'expect_staff', 'expect_firs'),
    [
        # Control Center returns lowercase role identifiers (pluck('role')).
        ({'Norway': ['mentor']}, True, False, False, ['Norway']),
        ({'Norway': ['buddy']}, False, True, False, []),
        ({'Norway': ['moderator']}, False, False, True, []),
        (
            {'Denmark': ['mentor'], 'Sweden': ['buddy'], 'Norway': ['moderator']},
            True,
            True,
            True,
            ['Denmark'],
        ),
        # Case-insensitivity: legacy capitalised group names must still match.
        ({'Norway': ['Mentor']}, True, False, False, ['Norway']),
        # Areas with no roles are null and must be skipped safely.
        ({'Norway': None}, False, False, False, []),
    ],
)
def test_get_mentor_roles_detects_case_insensitive_roles(
    cog: RolesCog,
    roles_payload: dict,
    expect_mentor: bool,
    expect_buddy: bool,
    expect_staff: bool,
    expect_firs: list[str],
) -> None:
    data = [{'id': CID, 'roles': roles_payload}]

    info = cog.get_mentor_roles(CID, data)

    assert info.mentor_should_be is expect_mentor
    assert info.buddy_should_be is expect_buddy
    assert info.training_staff_should_be is expect_staff
    assert info.mentor_firs == expect_firs


def test_get_mentor_roles_ignores_other_users(cog: RolesCog) -> None:
    data = [{'id': 7654321, 'roles': {'Norway': ['mentor']}}]

    info = cog.get_mentor_roles(CID, data)

    assert info.mentor_should_be is False
