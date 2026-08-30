import asyncio

import pytest

from cogs.cc_roles import CCRolesCog
from helpers.config import Config, config
from tests.conftest import FakeMember, FakeRole

DENMARK = FakeRole(1, 'Denmark')
NORWAY = FakeRole(2, 'Norway')


@pytest.fixture
def cog() -> CCRolesCog:
    # Bypass __init__ so we don't start the background task loop; get_mentor_roles
    # is a pure function of its arguments and needs no bot/loop state.
    return CCRolesCog.__new__(CCRolesCog)


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
    cog: CCRolesCog,
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


def test_get_mentor_roles_ignores_other_users(cog: CCRolesCog) -> None:
    data = [{'id': 7654321, 'roles': {'Norway': ['mentor']}}]

    info = cog.get_mentor_roles(CID, data)

    assert info.mentor_should_be is False


def test_get_mentor_roles_uses_configured_cc_roles(
    cog: CCRolesCog, monkeypatch: pytest.MonkeyPatch
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
    cog: CCRolesCog, monkeypatch: pytest.MonkeyPatch
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


def test_training_roles_merges_repeated_countries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # TRAINING_DATA is comma separated, so a country with several ratings is
    # listed once per rating. Every rating must survive the parse.
    monkeypatch.setenv('TRAINING_DATA', 'Denmark|S2:1,Norway|S1:2,Norway|S2:3')

    parsed = Config()

    assert parsed.TRAINING_ROLES == {
        'Denmark': {'S2': '1'},
        'Norway': {'S1': '2', 'S2': '3'},
    }


def test_update_fir_roles_removes_fir_the_member_no_longer_holds(
    cog: CCRolesCog, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A mentor who moves from Denmark to Norway must lose the Denmark role.
    monkeypatch.setattr(config, 'FIR_MENTORS', {'Denmark': '1', 'Norway': '2'})
    user = FakeMember(guild_roles=[DENMARK, NORWAY], roles=[DENMARK])

    asyncio.run(cog.update_fir_roles(user, ['Norway'], 'mentor', True))

    assert user.roles == [NORWAY]


def test_update_fir_roles_removes_all_firs_when_role_revoked(
    cog: CCRolesCog, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, 'FIR_MENTORS', {'Denmark': '1', 'Norway': '2'})
    user = FakeMember(guild_roles=[DENMARK, NORWAY], roles=[DENMARK, NORWAY])

    asyncio.run(cog.update_fir_roles(user, [], 'mentor', False))

    assert user.roles == []


def test_missing_cc_datasets_names_empty_and_failed_fetches(cog: CCRolesCog) -> None:
    # None is a failed fetch, [] is a successful but empty one. Acting on either
    # would strip managed roles from every member.
    missing = cog.missing_cc_datasets(
        {
            'roles': [{'id': CID}],
            'training': [],
            'endorsements': None,
            'atc_activity': [{'id': CID}],
        }
    )

    assert missing == ['training', 'endorsements']


def test_missing_cc_datasets_is_empty_when_all_datasets_have_data(
    cog: CCRolesCog,
) -> None:
    missing = cog.missing_cc_datasets(
        {
            'roles': [{'id': CID}],
            'training': [{'id': CID}],
            'endorsements': [{'id': CID}],
            'atc_activity': [{'id': CID}],
        }
    )

    assert missing == []


DENMARK_S3 = FakeRole(11, 'Denmark S3')
DENMARK_C1 = FakeRole(12, 'Denmark C1')
DENMARK_CTR = FakeRole(13, 'Denmark Controller')
NORWAY_CTR = FakeRole(14, 'Norway Controller')

ATC_GUILD_ROLES = [DENMARK_S3, DENMARK_C1, DENMARK_CTR, NORWAY_CTR]


@pytest.fixture
def atc_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        config, 'RATING_FIR_DATA', {'Denmark': {'S3': '11', 'C1': '12'}}
    )
    monkeypatch.setattr(
        config, 'CONTROLLER_FIR_ROLES', {'Denmark': '13', 'Norway': '14'}
    )


def test_update_fir_atc_roles_swaps_the_role_when_the_rating_changes(
    cog: CCRolesCog, atc_config: None
) -> None:
    # A controller promoted from S3 to C1 must lose the S3 role for that FIR.
    user = FakeMember(guild_roles=ATC_GUILD_ROLES, roles=[DENMARK_S3, DENMARK_CTR])
    data = [{'id': CID, 'atc_active_areas': {'denmark': True}, 'rating': 'C1'}]

    asyncio.run(cog.update_fir_atc_roles(user, CID, data))

    assert sorted(role.id for role in user.roles) == [12, 13]


def test_update_fir_atc_roles_removes_firs_absent_from_the_payload(
    cog: CCRolesCog, atc_config: None
) -> None:
    # onlyAtcActive means an area the member is no longer active in simply drops
    # out of the payload; the role must still be removed.
    user = FakeMember(
        guild_roles=ATC_GUILD_ROLES, roles=[DENMARK_S3, DENMARK_CTR, NORWAY_CTR]
    )
    data = [{'id': CID, 'atc_active_areas': {'denmark': True}, 'rating': 'S3'}]

    asyncio.run(cog.update_fir_atc_roles(user, CID, data))

    assert sorted(role.id for role in user.roles) == [11, 13]


def test_update_fir_atc_roles_clears_everything_without_an_entry(
    cog: CCRolesCog, atc_config: None
) -> None:
    user = FakeMember(
        guild_roles=ATC_GUILD_ROLES, roles=[DENMARK_S3, DENMARK_CTR, NORWAY_CTR]
    )

    asyncio.run(cog.update_fir_atc_roles(user, CID, []))

    assert user.roles == []
