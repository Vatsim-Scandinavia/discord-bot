import os

import discord
import requests
import re

from discord import InvalidArgument
from discord.ext import commands
from discord_slash import SlashCommand
from dotenv import load_dotenv
from helpers.config import VATSCA_MEMBER_ROLE, VATSIM_MEMBER_ROLE, GUILD_ID
from helpers import config

load_dotenv('.env')

BOT_TOKEN = str(os.getenv('BOT_TOKEN'))

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=config.PREFIXES, description=config.DESCRIPTION, intents=intents, help_command=None, case_insensitive=True)

slash = SlashCommand(bot, sync_commands=True)

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

@bot.event
async def on_member_update(before_update, user: discord.User):
    """
    Function checks member and assigns role according to the username
    :param before_update:
    :param user:
    :return:
    """
    # Nothing here for now, will put back when API is working again

    

@bot.event
async def on_connect():
    config.load_cogs(bot)

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f'Error starting the bot. Exception - {e}')