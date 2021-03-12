import discord
from dotenv import load_dotenv

load_dotenv('.env')

PREFIXES = [
    '!', '.', '?', '#'
]

DESCRIPTION = 'This is a new VATSCA Discord Bot'

PRESENCE_TEXT = 'VATSCA Airspace'

COGS = [
    'cogs.admin',
    'cogs.member',
    'cogs.announcement',
    'cogs.tasks',
    'cogs.events',
    'cogs.update_welcome_message',
    'cogs.update_countries_message',
    'cogs.update_notification_message',
    'cogs.vtc',
]

COGS_LOAD = {
    'admin': 'cogs.admin',
    'member': 'cogs.member',
    'announcement': 'cogs.announcement',
    'check_members': 'cogs.tasks',
    'events': 'cogs.events',
    'welcome': 'cogs.update_welcome_message',
    'countries': 'cogs.update_countries_message',
    'notification': 'cogs.update_notification_message',
    'vtc': 'cogs.vtc',
}

VATSIM_MEMBER_ROLE = "Vatsim Member"

CHECK_MEMBERS_INTERVAL = 86400

POST_EVENTS_INTERVAL = 900

VATSCA_MEMBER_ROLE = 817310145737523210

EVENTS_ROLE = 817310403469639750

ADMIN_ROLES = [
    'web team',
    'admin',
]

EVENTS_CHANNEL = 817306386245484544

VATSCA_BLUE = 0x43c6e7

ROLE_REASONS = {
    'vatsca_add': 'Member is now part of VATSCA',
    'vatsca_remove': 'Member is no longer part of VATSCA',
    'no_cid': 'User does not have a VATSIM ID in his/her nickname.',
    'no_auth': 'User did not authenticate via the Community Website',
}

RULES_CHANNEL = 817306790726991882

CHECK_RULES_INTERVAL = 60

ROLES_CHANNEL = 817306842232913941

GUILD_ID = 817306248411742229

VTC_CHANNEL = 817306917155504128

VTC_STAFFING_MSG = 817335568937123860

S1 = 817310520948162560

S2 = 817310551646404638

S3 = 817310644927201302

C1 = 817310761671458816

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