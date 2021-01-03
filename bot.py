import os

import discord
from discord import InvalidArgument
from discord.ext import commands
from dotenv import load_dotenv

from helpers import config

load_dotenv('.env')

BOT_TOKEN = str(os.getenv('BOT_TOKEN'))

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=config.PREFIXES, description=config.DESCRIPTION, intents=intents, help_command=None)

config.load_cogs(bot)

"""
    Bot event that sets bots rich presence in Discord profile
"""


@bot.event
async def on_ready() -> None:
    print(f'Bot started. \nUsername: {bot.user.name}. \nID: {bot.user.id}')

    try:
        await bot.change_presence(activity=config.activity(), status=config.status())

        print('Presence changed.')
    except InvalidArgument as e:
        print(f'Error changing presence. Exception - {e}')


if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f'Error starting the bot. Exception - {e}')
