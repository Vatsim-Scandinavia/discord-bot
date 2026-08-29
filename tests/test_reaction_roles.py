import asyncio

import pytest

from cogs.reaction_roles import ReactionRolesCog
from helpers.config import config
from tests.conftest import FakeBot, FakeMember, FakeReactionPayload, FakeRole

GUILD_ID = 100
MESSAGE_ID = 555
USER_ID = 42
STAR = '⭐'


@pytest.fixture
def fir_role() -> FakeRole:
    return FakeRole(1, 'Denmark')


@pytest.fixture(autouse=True)
def reaction_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, 'REACTION_MESSAGE_IDS', [str(MESSAGE_ID)])
    monkeypatch.setattr(config, 'REACTION_ROLES', {':star:': '1'})


def build(member: FakeMember) -> ReactionRolesCog:
    cog = ReactionRolesCog.__new__(ReactionRolesCog)
    cog.bot = FakeBot(member.guild)
    return cog


def payload(
    emoji_name: str = STAR, message_id: int = MESSAGE_ID
) -> FakeReactionPayload:
    return FakeReactionPayload(GUILD_ID, USER_ID, message_id, emoji_name)


def test_reaction_add_grants_the_configured_role(fir_role: FakeRole) -> None:
    member = FakeMember(guild_roles=[fir_role], roles=[], member_id=USER_ID)

    asyncio.run(build(member).handle_role_reaction(payload(), 'add'))

    assert member.roles == [fir_role]
    assert len(member.dms) == 1


def test_reaction_remove_revokes_the_configured_role(fir_role: FakeRole) -> None:
    member = FakeMember(guild_roles=[fir_role], roles=[fir_role], member_id=USER_ID)

    asyncio.run(build(member).handle_role_reaction(payload(), 'remove'))

    assert member.roles == []
    assert len(member.dms) == 1


def test_reaction_on_unconfigured_message_is_ignored(fir_role: FakeRole) -> None:
    member = FakeMember(guild_roles=[fir_role], roles=[], member_id=USER_ID)

    asyncio.run(build(member).handle_role_reaction(payload(message_id=999), 'add'))

    assert member.roles == []
    assert member.dms == []


def test_reaction_with_unconfigured_emoji_is_ignored(fir_role: FakeRole) -> None:
    member = FakeMember(guild_roles=[fir_role], roles=[], member_id=USER_ID)

    asyncio.run(build(member).handle_role_reaction(payload(emoji_name='🔨'), 'add'))

    assert member.roles == []
    assert member.dms == []
