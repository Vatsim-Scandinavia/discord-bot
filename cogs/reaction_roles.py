"""Lets members opt in to a FIR and its channels by reacting to a message."""

from typing import Literal

import discord
import emoji
import structlog
from discord.ext import commands

from core.exceptions import GuildNotFound
from core.roles import send_dm, update_role
from helpers.config import config

logger = structlog.stdlib.get_logger()


class ReactionRolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_role_reaction(
        self, payload: discord.RawReactionActionEvent, action: Literal['add', 'remove']
    ):
        """Grant or revoke the role mapped to the reacted emoji."""
        if not payload.guild_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            raise GuildNotFound(payload.guild_id, payload)

        user = guild.get_member(payload.user_id)
        if not user:
            return

        emoji_name = emoji.demojize(payload.emoji.name)
        message_id = str(payload.message_id)

        # Keyed by the pair: the same emoji may drive a different role on another
        # message, and grants nothing on a message it is not configured for.
        configured_role_id = config.REACTION_ROLE_MAP.get((message_id, emoji_name))
        if configured_role_id is None:
            return

        role_id = int(configured_role_id)
        role = discord.utils.get(guild.roles, id=role_id)
        if not role:
            logger.warning('Reaction role not found in guild', role_id=role_id)
            return

        if action == 'add' and role not in user.roles:
            await update_role(
                user,
                role,
                True,
                config.ROLE_REASONS['reaction_add'],
                config.ROLE_REASONS['reaction_remove'],
            )
            await send_dm(
                user,
                f'You have been given the `{role.name}` role because you reacted with {payload.emoji}',
            )

        if action == 'remove' and role in user.roles:
            await update_role(
                user,
                role,
                False,
                config.ROLE_REASONS['reaction_add'],
                config.ROLE_REASONS['reaction_remove'],
            )
            await send_dm(
                user,
                f'You no longer have the `{role.name}` role because you removed your reaction.',
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Event listener for adding roles based on reactions."""
        if self.bot.user and payload.user_id == self.bot.user.id:
            return
        await self.handle_role_reaction(payload, 'add')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Event listener for removing roles based on reactions."""
        if self.bot.user and payload.user_id == self.bot.user.id:
            return
        await self.handle_role_reaction(payload, 'remove')


async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRolesCog(bot))
