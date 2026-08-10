import pytest

from cogs.roles import RolesCog
from helpers.config import config


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


def test_get_mentor_roles_uses_configured_cc_roles(
    cog: RolesCog, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Operators can rename the CC identifiers that map to each Discord role.
    monkeypatch.setattr(config, 'CC_MENTOR_ROLES', {'coach'})
    monkeypatch.setattr(config, 'CC_BUDDY_ROLES', {'sidekick'})
    monkeypatch.setattr(config, 'CC_TRAINING_ROLES', {'staff'})

    data = [
        {
            'id': CID,
            'roles': {
                'Norway': ['coach'],
                'Denmark': ['sidekick'],
                'Sweden': ['staff'],
            },
        }
    ]

    info = cog.get_mentor_roles(CID, data)

    assert info.mentor_should_be is True
    assert info.mentor_firs == ['Norway']
    assert info.buddy_should_be is True
    assert info.buddy_firs == ['Denmark']
    assert info.training_staff_should_be is True


def test_get_mentor_roles_supports_multiple_cc_roles_per_discord_role(
    cog: RolesCog, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A single Discord role can be driven by several CC identifiers, and the
    # per-FIR lists must aggregate matches from every configured identifier.
    monkeypatch.setattr(config, 'CC_MENTOR_ROLES', frozenset({'mentor', 'coach'}))
    monkeypatch.setattr(config, 'CC_BUDDY_ROLES', frozenset({'buddy', 'sidekick'}))
    # Training staff is a guild-wide boolean (no FIR dimension), so we only
    # assert it flips on when any configured identifier matches.
    monkeypatch.setattr(config, 'CC_TRAINING_ROLES', frozenset({'moderator', 'staff'}))

    data = [
        {
            'id': CID,
            'roles': {
                'Norway': ['mentor'],
                'Denmark': ['coach'],
                'Sweden': ['buddy'],
                'Finland': ['sidekick'],
                'Iceland': ['staff'],
            },
        }
    ]

    info = cog.get_mentor_roles(CID, data)

    assert info.mentor_should_be is True
    assert info.mentor_firs == ['Norway', 'Denmark']
    assert info.buddy_should_be is True
    assert info.buddy_firs == ['Sweden', 'Finland']
    assert info.training_staff_should_be is True


@pytest.mark.parametrize('raw', ['', '   ', ' , ,'])
def test_parse_cc_roles_falls_back_to_default_when_effectively_empty(
    raw: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv('CC_MENTOR_ROLES', raw)

    assert config._parse_cc_roles('CC_MENTOR_ROLES', 'mentor') == frozenset({'mentor'})


def test_parse_cc_roles_returns_immutable_lowercased_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv('CC_MENTOR_ROLES', 'Mentor, Coach ')

    result = config._parse_cc_roles('CC_MENTOR_ROLES', 'mentor')

    assert result == frozenset({'mentor', 'coach'})
    assert isinstance(result, frozenset)
