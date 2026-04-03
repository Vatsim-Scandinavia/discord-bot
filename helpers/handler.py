import re
from typing import TypedDict

import aiohttp
import discord
from discord.ext import commands

from helpers.config import config

MIN_VATSIM_CID = 800000


class DivisionMember(TypedDict):
    """Division member data."""

    id: int
    subdivision: str


class VATSIMDivisionMemberFetchException(Exception):
    def __init__(self) -> None:
        super().__init__('An error occurred while fetching VATSIM division members.')


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

    @classmethod
    async def get_division_members(cls) -> list[DivisionMember]:
        """
        Fetch all division members from the API with pagination.
        :return:
        """
        result: list[DivisionMember] = []
        url = config.VATSIM_CHECK_MEMBER_URL  # Initialize from config

        if not url:  # Ensure the URL is defined
            raise ValueError('VATSIM_CHECK_MEMBER_URL is not configured or is None')

        async with aiohttp.ClientSession() as session:
            while url:
                # We'd like to capture any non-valid responses sooner rather than earlier
                try:
                    data, url = await cls._fetch_page(session, url)
                except Exception as e:
                    raise VATSIMDivisionMemberFetchException from e

                # Stop if data is not available or an error occurred
                if not data:
                    break

                result.extend(data)

        return result

    @staticmethod
    async def _fetch_page(session: aiohttp.ClientSession, url):
        """
        Fetch data from a single page and return the next URL if available.

        Note: Fails hard and early if at any point a request fails.
        """
        headers = {
            'Authorization': f'Token {config.VATSIM_API_TOKEN}',
        }

        async with session.get(url, headers=headers) as response:
            response.raise_for_status()

            try:
                feedback = await response.json()
            except Exception as e:
                raise Exception('An error occurred while parsing JSON') from e
            data = feedback.get('results', [])
            next_url = feedback.get('next')

            # Replace http with https if needed
            if next_url and next_url.startswith('http://'):
                next_url = next_url.replace('http://', 'https://')

            return data, next_url

    @staticmethod
    def get_cid(member: discord.Member) -> int | None:
        """
        Get CID based on VATSIM Discord member.

        Args:
            member: The Discord guild member.

        Returns:
            None if the member does not have the VATSIM member role, otherwise the CID.

        Raises:
            ValueError: If the member has the VATSIM member role but a valid CID cannot be extracted from their nickname.

        """
        if config.VATSIM_MEMBER_ROLE not in [role.id for role in member.roles]:
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
