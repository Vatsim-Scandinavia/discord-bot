import asyncio

import discord
from discord.errors import HTTPException
from discord.ext import commands
from discord.ext.commands import Bot

from helpers.config import config

class PublishMessageException(Exception):
    def __init__(self) -> None:
        super().__init__("An error occurred while trying to publish a message.")
    

class Publisher(commands.Cog):
    """Publishes messages sent to a given channel for subscribers to see."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == config.EVENTS_CHANNEL:
            await self.crosspost(self, message)

    async def crosspost(self, message: discord.Message, retries = 3) -> None:
        """
        Safely crossposts a message, with rate limit handling.
        :param message: The discord message to crosspost.
        :param retries: Number of retries allowed in case of rate limiting.
        """

        for _attempt in range(retries):
            try:
                await message.publish()
                return
            
            except HTTPException as e:
                if e.status == 429:
                    retry_after = e.retry_after if hasattr(e, 'retry_after') else 500 # Default to 500 seconds if not provided
                    print(f'Rate limit hit! Retrying in {retry_after:.2f} seconds...', flush=True)
                    await asyncio.sleep(retry_after)

                else:
                    raise PublishMessageException from e

            except Exception as e:
                raise PublishMessageException from e
        
        print(f"Failed to publish message after {retries} attempts", flush=True)


async def setup(bot: Bot) -> None:
    await bot.add_cog(Publisher(bot))

    