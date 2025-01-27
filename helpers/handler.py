import discord
import aiohttp
import re

from discord.ext import commands
from helpers.config import config


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
        else:
            return True

    async def get_division_members(self):
        """
        Fetch all division members from the API with pagination.
        :return:
        """
        result = []
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

    async def get_cid(self, user):
        """
        Get CID based on user discord ID

        Args:
            user (discord.Member): The Discord member object.
        """
        cid = re.findall(r'\d+', str(user.nick))

        if len(cid) < 1:
            raise ValueError

        return int(cid[0])
