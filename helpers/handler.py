import discord
import aiohttp

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
    
    async def get_division_members(self):
        """
        Fetch all division members from the API with pagination.
        :return:
        """
        result = []
        url = config.VATSIM_CHECK_MEMBER_URL

        # Initialize an aiohttp session for async requests
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
                    next_url = data.get('next')
                    return data, next_url

                else:
                    print(f"Failed to fetch page: {url}. Status code: {response.status}")
                    return [], None
        
        except aiohttp.ClientError as e:
            print(f"An error occurred: {e}")
            return [], None
        
    async def get_cid(user):
        """
        Get CID based on user discord ID
        
        Args:
            user (discord.Member): The Discord member object.
        """
        url = f"https://api.vatsim.net/v2/members/discord/{user.id}"
        headers = {
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession as session:
            try:
                async with session.get(url, headers=headers, params="") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("user_id")
                        
                    else:
                        print(f"Failed to fetch CID for user {user.id}. Status code: {response.status}")

            except aiohttp.ClientError as e:
                print(f"HTTP error occurred while accessing {url}: {e}")
                return None
        

