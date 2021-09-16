import os

import discord
import requests
import re

from discord import InvalidArgument
from discord.ext import commands
from discord_slash import SlashCommand
from dotenv import load_dotenv
from helpers.config import VATSCA_MEMBER_ROLE, VATSIM_MEMBER_ROLE, VATSIM_SUBDIVISION, GUILD_ID, BOT_TOKEN
from helpers.members import get_division_members
from helpers import config

load_dotenv('.env')

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='/', description=config.DESCRIPTION, intents=intents, help_command=None, case_insensitive=True)

slash = SlashCommand(bot, sync_commands=True)

"""
    Bot event that sets bots rich presence in Discord profile
"""
@bot.event
async def on_ready() -> None:
    print(f'Bot started. \nUsername: {bot.user.name}. \nID: {bot.user.id}')

    try:
        await bot.change_presence(activity=config.activity(), status=config.status())
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

    # Check if the nick has been changed as it's usually the only thing we care about
    if(before_update.nick == user.nick):
        return

    guild = bot.get_guild(GUILD_ID)

    vatsca_member = discord.utils.get(guild.roles, id=VATSCA_MEMBER_ROLE)
    vatsim_member = discord.utils.get(guild.roles, id=VATSIM_MEMBER_ROLE)

    if vatsim_member not in user.roles:
        if vatsca_member in user.roles:
            await user.remove_roles(vatsca_member)
    try:

        cid = re.findall('\d+', str(user.nick))

        if len(cid) < 1:
            raise ValueError

        api_data = await get_division_members()

        for entry in api_data:
            if entry['id'] == str(cid[0]):
                if vatsca_member not in user.roles and entry["subdivision"] == VATSIM_SUBDIVISION:
                    await user.add_roles(vatsca_member)
                elif vatsca_member in user.roles and entry["subdivision"] != VATSIM_SUBDIVISION:
                    await user.remove_roles(vatsca_member)
                
                break

    except ValueError as e:
        # This happens when a CID is not found, ignore it
        print("Tried to find an ID but it threw a ValueError, not found")

    except Exception as e:
        print(e)

    

@bot.event
async def on_connect():
    config.load_cogs(bot)

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f'Error starting the bot. Exception - {e}')