import re
from typing import TypedDict

import aiohttp
import discord
from discord.ext import commands

from helpers.config import config


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

    async def get_context(
        self, bot, interaction: discord.Interaction
    ) -> commands.Context:
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

    async def get_division_members(self) -> list[DivisionMember]:
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
                    data, url = await self._fetch_page(session, url)
                except Exception as e:
                    raise VATSIMDivisionMemberFetchException from e

                # Stop if data is not available or an error occurred
                if not data:
                    break

                result.extend(data)

        return result

    async def _fetch_page(self, session: aiohttp.ClientSession, url):
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

    def get_cid(self, member: discord.Member):
        """
        Get CID based on VATSIM Discord member.

        Args:
            member: The Discord guild member.

        """
        cid = re.findall(r'\d+', str(member.nick))

        if len(cid) < 1:
            raise ValueError

        return int(cid[0])

    def get_name(self, member: discord.Member) -> str | None:
        """
        Get presentation name based on VATSIM Discord member.

        Args:
            member: The Discord guild member.

        """
        name = re.findall(r'.+?(?= -)', str(member.nick))
        if not name:
            return None

        return name[0]
