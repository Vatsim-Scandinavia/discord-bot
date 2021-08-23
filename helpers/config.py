import discord
import os
from dotenv import load_dotenv

load_dotenv('.env')

PREFIXES = [
    '!', '.', '?', '#'
]

DESCRIPTION = 'This is a new VATSCA Discord Bot'
PRESENCE_TEXT = 'VATSCA Airspace'

VATSCA_BLUE = 0x43c6e7

COGS = [
    'cogs.admin',
    'cogs.member',
    #'cogs.announcement',
    'cogs.tasks',
    'cogs.events',
    'cogs.update_messages',
    'cogs.staffing'
]

COGS_LOAD = {
    'admin': 'cogs.admin',
    'member': 'cogs.member',
    #'announcement': 'cogs.announcement',
    'check_members': 'cogs.tasks',
    'events': 'cogs.events',
    'update': 'cogs.update_messages',
    'staffing': 'cogs.staffing'
}

ADMIN_ROLES = [
    'Web',
    'Discord Moderator',
    'Discord Administrator',
]

STAFF_ROLES = [
    'Web',
    'Discord Moderator',
    'Discord Administrator',
    'Board',
    'Staff',
]

ROLE_REASONS = {
    'vatsca_add': 'Member is now part of VATSCA',
    'vatsca_remove': 'Member is no longer part of VATSCA',
    'no_cid': 'User does not have a VATSIM ID in his/her nickname.',
    'no_auth': 'User did not authenticate via the Community Website',
}

AVAILABLE_EVENT_DAYS = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday'
]

# Environment variables
DEBUG = os.getenv('DEBUG')

BOT_TOKEN = str(os.getenv('BOT_TOKEN'))
FORUM_API_TOKEN = os.getenv('FORUM_API_TOKEN')
VATSIM_API_TOKEN = str(os.getenv('VATSIM_API_TOKEN'))

EVENT_CALENDAR_URL = str(os.getenv('EVENT_CALENDAR_URL'))
EVENT_CALENDAR_TYPE = int(os.getenv('EVENT_CALENDAR_TYPE'))

VATSIM_CHECK_MEMBER_URL = str(os.getenv('VATSIM_CHECK_MEMBER_URL'))
DIVISION_URL = str(os.getenv('DIVISION_URL'))

BOT_DB_HOST = str(os.getenv('BOT_DB_HOST'))
BOT_DB_USER = str(os.getenv('BOT_DB_USER'))
BOT_DB_PASSWORD = str(os.getenv('BOT_DB_PASSWORD'))
BOT_DB_NAME = str(os.getenv('BOT_DB_NAME'))

VATSCA_MEMBER_ROLE = int(os.getenv('VATSCA_MEMBER_ROLE'))
VATSIM_MEMBER_ROLE = int(os.getenv('VATSIM_MEMBER_ROLE'))
EVENTS_ROLE = int(os.getenv('EVENTS_ROLE'))

GUILD_ID = int(os.getenv('GUILD_ID'))
STAFFING_INTERVAL = int(os.getenv('STAFFING_INTERVAL'))

EVENTS_CHANNEL = int(os.getenv('EVENTS_CHANNEL'))
RULES_CHANNEL = int(os.getenv('RULES_CHANNEL'))
ROLES_CHANNEL = int(os.getenv('ROLES_CHANNEL'))

BOT_CHANNEL = int(os.getenv('BOT_CHANNEL'))

CHECK_MEMBERS_INTERVAL = int(os.getenv('CHECK_MEMBERS_INTERVAL', 86400))
POST_EVENTS_INTERVAL = int(os.getenv('POST_EVENTS_INTERVAL', 30))
GET_EVENTS_INTERVAL = int(os.getenv('GET_EVENTS_INTERVAL', 900))
DELETE_EVENTS_INTERVAL = int(os.getenv('DELETE_EVENTS_INTERVAL'))

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
