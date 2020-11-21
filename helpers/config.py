import discord
from dotenv import load_dotenv
import os

load_dotenv('.env')

PREFIXES = [
    '!', '.', '?',
]

DESCRIPTION = 'This is a new VATSCA Discord Bot'

PRESENCE_TEXT = 'VATSCA Airspace'

COGS = [
    'cogs.admin',
    'cogs.member',
    'cogs.announcement',
    'cogs.tasks',
    'cogs.events',
]

VATSIM_MEMBER_ROLE = "Vatsim Member"

CHECK_MEMBERS_INTERVAL = 86400

POST_EVENTS_INTERVAL = 60

VATSCA_MEMBER_ROLE = 778356499335479338

ADMIN_ROLES = [
    'web team',
    'admin',
]


def prefix() -> list:
    return PREFIXES


def activity() -> discord.Activity:
    return discord.Activity(type=discord.ActivityType.watching, name=PRESENCE_TEXT)


def status() -> discord.Status:
    return discord.Status.online


def load_cogs(bot: discord.ext.commands.Bot) -> None:
    for cog in COGS:
        try:
            bot.load_extension(cog)
        except Exception as e:
            print(f'Failed to load cog - {cog}. \n Error: {e}')