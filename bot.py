import os
import sentry_sdk

import discord
import requests
import re
import emoji

from discord import InvalidArgument
from discord.ext import commands
from discord_slash import SlashCommand
from dotenv import load_dotenv
from helpers.config import VATSCA_MEMBER_ROLE, VATSIM_MEMBER_ROLE, VATSIM_SUBDIVISION, GUILD_ID, BOT_TOKEN, REACTION_ROLES, REACTION_MESSAGE_IDS, REACTION_EMOJI, ROLE_REASONS
from helpers.members import get_division_members
from helpers import config

load_dotenv('.env')

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='/', description=config.DESCRIPTION, intents=intents, help_command=None, case_insensitive=True)

slash = SlashCommand(bot, sync_commands=True)

sentry_sdk.init(
    dsn="https://72a8a935ed0845cf97486216a196bf1c@o1103878.ingest.sentry.io/6614652",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)

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
    try:

        cid = re.findall('\d+', str(user.nick))

        if len(cid) < 1:
            raise ValueError

        api_data = await get_division_members()

        should_have_vatsca = False

        for entry in api_data:
            if int(entry['id']) == int(cid[0]) and str(entry["subdivision"]) == str(VATSIM_SUBDIVISION):
                should_have_vatsca = True

        if vatsim_member in user.roles:
            if vatsca_member not in user.roles and should_have_vatsca == True:
                await user.add_roles(vatsca_member)
            elif vatsca_member in user.roles and should_have_vatsca == False:
                await user.remove_roles(vatsca_member)
        elif vatsim_member not in user.roles and vatsca_member in user.roles:
            await user.remove_roles(vatsca_member)

    except ValueError as e:
        # This happens when a CID is not found, ignore it
        print("Tried to find an ID but it threw a ValueError, not found")

    except Exception as e:
        print(e)

@bot.event
async def on_raw_reaction_add(payload):
    channel = bot.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    guild = bot.get_guild(GUILD_ID)
    emojies = emoji.demojize(payload.emoji.name)
    for message in REACTION_MESSAGE_IDS:
        if int(msg.id) == int(message) and emojies in REACTION_EMOJI:
            role = discord.utils.get(guild.roles, id=int(REACTION_ROLES[emojies]))
            user = guild.get_member(payload.user_id)
            if role not in user.roles:
                await user.add_roles(role, reason=ROLE_REASONS['reaction_add'])
                await user.send(f'You have been given the `{role.name}` role because you reacted with {payload.emoji}')

@bot.event
async def on_raw_reaction_remove(payload):
    channel = bot.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    guild = bot.get_guild(GUILD_ID)
    emojies = emoji.demojize(payload.emoji.name)
    for message in REACTION_MESSAGE_IDS:
        if int(msg.id) == int(message) and emojies in REACTION_EMOJI:
            role = discord.utils.get(guild.roles, id=int(REACTION_ROLES[emojies]))
            user = guild.get_member(payload.user_id)
            if role in user.roles:
                await user.remove_roles(role, reason=ROLE_REASONS['reaction_remove'])
                await user.send(f'You no longer have the `{role.name}` role because you removed your reaction.')
    

@bot.event
async def on_connect():
    config.load_cogs(bot)

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f'Error starting the bot. Exception - {e}')