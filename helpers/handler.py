import discord
import aiohttp
import re

from discord.ext import commands
from helpers.config import config

class Handler():
    
    def __init__(self) -> None:
        pass

    async def get_context(self, bot, interaction: discord.Interaction) -> commands.Context:
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
            raise discord.app_commands.AppCommandError('You do not have the proper roles to use this command')
        else:
            return True

    async def get_division_members(self):
        """
        Fetch all division members from the API with pagination.
        :return:
        """
        result = []
        url = config.VATSIM_CHECK_MEMBER_URL  # Initialize from config

        if not url: # Ensure the URL is defined
            raise ValueError("VATSIM_CHECK_MEMBER_URL is not configured or is None")

        async with aiohttp.ClientSession() as session:
            while url:
                # Fetch data for each page
                data, url = await self._fetch_page(session, url)

                if data:
                    result.extend(data)
                
                else:
                    break # Stop if data is not available or an error occurred

        return result

    async def _fetch_page(self, session, url):
        """
        Fetch data from a single page and return the next URL if available.
        :return:
        """
        headers = {
            'Authorization': f'Token {config.VATSIM_API_TOKEN}',
        }

        try:

            async with session.get(url, headers=headers) as response:

                # Process the response
                if response.status == 200:
                    feedback = await response.json()

                    data = feedback.get('results', [])
                    next_url = feedback.get('next')

                    # Replace http with https if needed
                    if next_url and next_url.startswith('http://'):
                        next_url = next_url.replace('http://', 'https://')

                    return data, next_url
                    
                else:
                    print(f"Failed to fetch page. Status: {response.status}, URL: {url}")
                    return [], None
                    
        
        except aiohttp.ClientError as e:
            print(f"An error occurred: {e}")
            return [], None
        
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
        

