import re

import discord
from discord.ext import commands

from helpers.config import config
from helpers.vatsim_api import (
    MIN_VATSIM_CID,
    DivisionMember,
    VATSIMDivisionMemberFetchException,
    vatsim_api,
)

__all__ = [
    'MIN_VATSIM_CID',
    'DivisionMember',
    'Handler',
    'VATSIMDivisionMemberFetchException',
]


class Handler:
    def __init__(self) -> None:
        pass

    @staticmethod
    async def get_context(bot, interaction: discord.Interaction) -> commands.Context:
        """
        Helper function to get context from interaction
        :return:
        """
        ctx: commands.Context = await bot.get_context(interaction)
        interaction._baton = ctx

        return ctx

    @staticmethod
    def is_obs(interaction: discord.Interaction):
        """
        Function checks if user has OBS role
        :return:
        """
        obs_role = discord.utils.get(interaction.guild.roles, id=config.OBS_ROLE)
        if obs_role in interaction.user.roles:
            raise discord.app_commands.AppCommandError(
                'You do not have the proper roles to use this command'
            )
        return True

    @staticmethod
    async def get_division_members() -> list[DivisionMember]:
        """Fetch all division members from the VATSIM API, following pagination."""
        return await vatsim_api.get_division_members()

    @staticmethod
    def has_vatsim_member_role(member: discord.Member) -> bool:
        """
        Check the gate every CID lookup goes through.

        Members without a roles collection (e.g. test stand-ins) pass, so only
        a member known to lack the VATSIM member role is turned away.
        """
        roles = getattr(member, 'roles', None)
        return roles is None or any(
            getattr(role, 'id', role) == config.VATSIM_MEMBER_ROLE for role in roles
        )

    @staticmethod
    def get_cid(member: discord.Member) -> int | None:
        """
        Get CID based on VATSIM Discord member.

        Args:
            member: The Discord guild member.

        Returns:
            None if the member has a roles collection and does not have the VATSIM
            member role, otherwise the CID.

        Raises:
            ValueError: If the member has the VATSIM member role but a valid CID cannot be extracted from their nickname.

        """
        if not Handler.has_vatsim_member_role(member):
            return None

        if member.nick is None:
            raise ValueError

        cid = re.search(r'\|-(\d+)-\|', member.nick)
        if cid:
            candidate = int(cid.group(1))
            if candidate >= MIN_VATSIM_CID:
                return candidate

        cid = re.search(r' - (\d+)\s*$', member.nick)
        if cid:
            candidate = int(cid.group(1))
            if candidate >= MIN_VATSIM_CID:
                return candidate

        cid = [
            int(candidate)
            for candidate in re.findall(r'\d+', member.nick)
            if int(candidate) >= MIN_VATSIM_CID
        ]

        if len(cid) < 1:
            raise ValueError

        return cid[-1]

    @staticmethod
    def get_name(member: discord.Member) -> str | None:
        """
        Get presentation name based on VATSIM Discord member.

        Args:
            member: The Discord guild member.

        """
        name = re.findall(r'.+?(?= -)', str(member.nick))
        if not name:
            return None

        return name[0]
