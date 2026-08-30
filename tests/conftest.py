import sys
from pathlib import Path

import discord

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class FakeRole:
    def __init__(self, role_id: int, name: str = 'role') -> None:
        self.id = role_id
        self.name = name


class FakeGuild:
    def __init__(self, roles: list[FakeRole]) -> None:
        self.roles = roles
        self._members: dict[int, FakeMember] = {}

    def add_member(self, member: 'FakeMember') -> None:
        self._members[member.id] = member

    def get_member(self, user_id: int) -> 'FakeMember | None':
        return self._members.get(user_id)


class FakeMember:
    """Minimal stand-in for discord.Member that records role changes and DMs."""

    def __init__(
        self,
        guild_roles: list[FakeRole],
        roles: list[FakeRole],
        member_id: int = 42,
    ) -> None:
        self.id = member_id
        self.name = 'tester'
        self.nick = None
        self.roles = list(roles)
        self.dms: list[str] = []
        self.guild = FakeGuild(guild_roles)
        self.guild.add_member(self)

    async def add_roles(self, *roles: FakeRole, reason: str = '') -> None:
        self.roles.extend(role for role in roles if role not in self.roles)

    async def remove_roles(self, *roles: FakeRole, reason: str = '') -> None:
        self.roles = [role for role in self.roles if role not in roles]

    async def send(self, message: str) -> None:
        self.dms.append(message)


class FakeBot:
    def __init__(self, guild: FakeGuild) -> None:
        self._guild = guild
        self.user = FakeRole(999, 'bot')

    def get_guild(self, guild_id: int) -> FakeGuild | None:
        return self._guild


class FakeEmoji:
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        """Render as the raw emoji, the way discord.py does."""
        return self.name


class FakeReactionPayload:
    def __init__(
        self,
        guild_id: int,
        user_id: int,
        message_id: int,
        emoji_name: str,
        channel_id: int = 1,
    ) -> None:
        self.guild_id = guild_id
        self.user_id = user_id
        self.message_id = message_id
        self.channel_id = channel_id
        self.emoji = FakeEmoji(emoji_name)


class FakeChannel:
    """Records what the bot posts, standing in for a text channel."""

    def __init__(self, channel_id: int = 1) -> None:
        self.id = channel_id
        self.sent: list[tuple[str, object]] = []
        self.replied_to: list[object] = []
        self.refuse_send = False
        self.posted: list[FakeMessage] = []
        self.refuse_reactions = False
        self.refused_reactions: list[str] = []
        """Emoji this channel turns down, when only some of them fail."""

    async def send(
        self,
        content: str,
        embed: object = None,
        reference: object = None,
        mention_author: bool = True,
    ) -> 'FakeMessage':
        if self.refuse_send:
            raise discord.HTTPException(FakeResponse(), 'missing permissions')

        self.sent.append((content, embed))
        self.replied_to.append(reference)
        self.posted.append(FakeMessage('', self, message_id=len(self.sent)))

        return self.posted[-1]


class FakeAuthor:
    def __init__(self, roles: list[FakeRole] | None = None, bot: bool = False) -> None:
        self.roles = roles or []
        self.bot = bot
        self.mention = '@tester'


class FakeMessage:
    def __init__(
        self,
        content: str,
        channel: FakeChannel | None = None,
        author: FakeAuthor | None = None,
        message_id: int = 1,
    ) -> None:
        self.id = message_id
        self.content = content
        self.channel = channel or FakeChannel()
        self.author = author or FakeAuthor()
        self.reactions: list[str] = []

    async def add_reaction(self, emoji: str) -> None:
        refused = getattr(self.channel, 'refused_reactions', [])

        if getattr(self.channel, 'refuse_reactions', False) or emoji in refused:
            raise discord.HTTPException(FakeResponse(), 'missing permissions')

        self.reactions.append(emoji)


class FakeInteractionResponse:
    def __init__(self) -> None:
        self.edits: list[str] = []
        self.messages: list[str] = []
        self.deferred = 0

    async def edit_message(self, content: str, view: object = None) -> None:
        self.edits.append(content)

    async def send_message(self, content: str, ephemeral: bool = False) -> None:
        self.messages.append(content)

    async def defer(self) -> None:
        self.deferred += 1


class FakeInteraction:
    def __init__(self) -> None:
        self.response = FakeInteractionResponse()


class FakeResponse:
    """Enough of an HTTP response for discord.HTTPException to accept."""

    status = 403
    reason = 'Forbidden'
