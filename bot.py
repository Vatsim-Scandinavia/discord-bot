import os

import discord
from discord import InvalidArgument
from discord.ext import commands
from discord_slash import SlashCommand
from dotenv import load_dotenv
import requests
import re
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
    guild = bot.get_guild(GUILD_ID)

    vatsca_member = discord.utils.get(guild.roles, id=VATSCA_MEMBER_ROLE)
    vatsim_member = discord.utils.get(guild.roles, name=VATSIM_MEMBER_ROLE)

    if vatsim_member not in user.roles:
        if vatsca_member in user.roles:
            await user.remove_roles(vatsca_member)
    try:

        cid = re.findall('\d+', str(user.nick))

        if len(cid[0]) < 6:
            raise ValueError

        statement = "https://api.vatsim.net/api/ratings/" + str(cid[0])
        request = requests.get(statement)
        if request.status_code == requests.codes.ok:
            request = request.json()
            

            if vatsca_member not in user.roles and request["subdivision"] == 'SCA':
                await user.add_roles(vatsca_member)
            elif vatsca_member in user.roles and request["subdivision"] != 'SCA':
                await user.remove_roles(vatsca_member)

    except ValueError as e:
        """if vatsca_member in user.roles:
            await user.remove_roles(vatsca_member)"""
        """if vatsim_member in user.roles:
            await user.remove_roles(vatsim_member)"""

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