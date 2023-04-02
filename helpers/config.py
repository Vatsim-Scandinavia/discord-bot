import discord
import os
from dotenv import load_dotenv
from distutils.util import strtobool

load_dotenv('.env')

DESCRIPTION = 'This is a new VATSCA Discord Bot'
PRESENCE_TEXT = 'VATSCA Airspace'

VATSCA_BLUE = 0x43c6e7

COGS = [
    'cogs.admin',
    'cogs.member',
    'cogs.tasks',
    'cogs.events',
    'cogs.update_messages',
    'cogs.staffings',
    'cogs.roles'
]

COGS_LOAD = {
    'admin': 'cogs.admin',
    'member': 'cogs.member',
    'check_members': 'cogs.tasks',
    'events': 'cogs.events',
    'update': 'cogs.update_messages',
    'staffings': 'cogs.staffings',
    'check_roles': 'cogs.roles'
}

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
    'mentor_add': 'Member is now a mentor',
    'mentor_remove': 'Member is no longer a mentor',
    'training_staff_add': 'Member is now Traning Staff',
    'training_staff_remove': 'Member is no longer Training Staff',
    'reaction_add': 'Member reacted to a message',
    'reaction_remove': 'Member removed a reaction from a message',
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
DEBUG = bool(strtobool(os.getenv('DEBUG', 'False')))

BOT_TOKEN = str(os.getenv('BOT_TOKEN'))
FORUM_API_TOKEN = os.getenv('FORUM_API_TOKEN')
VATSIM_API_TOKEN = str(os.getenv('VATSIM_API_TOKEN'))

EVENT_CALENDAR_URL = str(os.getenv('EVENT_CALENDAR_URL'))
EVENT_CALENDAR_TYPE = int(os.getenv('EVENT_CALENDAR_TYPE'))

CC_API_URL = str(os.getenv('CC_API_URL'))
CC_API_TOKEN = str(os.getenv('CC_API_TOKEN'))

VATSIM_CHECK_MEMBER_URL = str(os.getenv('VATSIM_CHECK_MEMBER_URL'))
VATSIM_SUBDIVISION = str(os.getenv('VATSIM_SUBDIVISION'))
DIVISION_URL = str(os.getenv('DIVISION_URL'))

BOT_DB_HOST = str(os.getenv('BOT_DB_HOST'))
BOT_DB_USER = str(os.getenv('BOT_DB_USER'))
BOT_DB_PASSWORD = str(os.getenv('BOT_DB_PASSWORD'))
BOT_DB_NAME = str(os.getenv('BOT_DB_NAME'))

SENTRY_KEY = str(os.getenv('SENTRY_KEY'))

VATSCA_MEMBER_ROLE = int(os.getenv('VATSCA_MEMBER_ROLE'))
VATSIM_MEMBER_ROLE = int(os.getenv('VATSIM_MEMBER_ROLE'))
EVENTS_ROLE = int(os.getenv('EVENTS_ROLE'))
MENTOR_ROLE = int(os.getenv('MENTOR_ROLE'))
TRAINING_STAFF_ROLE = int(os.getenv('TRAINING_STAFF_ROLE'))
OBS_ROLE = int(os.getenv('OBS_ROLE'))

FIR_DATA = str(os.getenv('FIR_DATA')).split(',')
FIRS = []
FIR_ROLES = []
for fir in FIR_DATA:
    FIRS.append(fir.split(':')[0])
    FIR_ROLES.append(fir.split(':')[1])

FIR_MENTORS = dict(zip(FIRS, FIR_ROLES))

REACTION_ROLE_DATA = str(os.getenv('REACTION_ROLE_DATA')).split(',')
REACTION_EMOJI = []
REACTION_MESSAGE_IDS = []
REACTION_ROLE_IDS = []
for reaction_role in REACTION_ROLE_DATA:
    REACTION_EMOJI.append(reaction_role.split('|')[0])
    REACTION_MESSAGE_IDS.append(reaction_role.split('|')[1])
    REACTION_ROLE_IDS.append(reaction_role.split('|')[2])

REACTION_ROLES = dict(zip(REACTION_EMOJI, REACTION_ROLE_IDS))

GUILD_ID = int(os.getenv('GUILD_ID'))
STAFFING_INTERVAL = int(os.getenv('STAFFING_INTERVAL'))

CHECK_MENTORS_INTERVAL = int(os.getenv('CHECK_MENTORS_INTERVAL'))

EVENTS_CHANNEL = int(os.getenv('EVENTS_CHANNEL'))
WELCOME_CHANNEL = int(os.getenv('WELCOME_CHANNEL'))
RULES_CHANNEL = int(os.getenv('RULES_CHANNEL'))
ROLES_CHANNEL = int(os.getenv('ROLES_CHANNEL'))

BOT_CHANNEL = int(os.getenv('BOT_CHANNEL'))

CHECK_MEMBERS_INTERVAL = int(os.getenv('CHECK_MEMBERS_INTERVAL', 86400))
POST_EVENTS_INTERVAL = int(os.getenv('POST_EVENTS_INTERVAL', 30))
GET_EVENTS_INTERVAL = int(os.getenv('GET_EVENTS_INTERVAL', 900))
DELETE_EVENTS_INTERVAL = int(os.getenv('DELETE_EVENTS_INTERVAL'))

def activity() -> discord.Activity:
    return discord.Activity(type=discord.ActivityType.watching, name=PRESENCE_TEXT)


def status() -> discord.Status:
    return discord.Status.online


async def load_cogs(bot: discord.ext.commands.Bot) -> None:
    for cog in COGS:
        try:
            await bot.load_extension(cog)
        except Exception as e:
            print(f'Failed to load cog - {cog}. \n Error: {e}')
