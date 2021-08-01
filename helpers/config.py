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
    'cogs.vtc',
]

COGS_LOAD = {
    'admin': 'cogs.admin',
    'member': 'cogs.member',
    #'announcement': 'cogs.announcement',
    'check_members': 'cogs.tasks',
    'events': 'cogs.events',
    'update': 'cogs.update_messages',
    'vtc': 'cogs.vtc',
}

VTC_POSITIONS = {
    'EKCH_DEL', 'ekch_del',
    'EKCH_A_GND', 'ekch_a_gnd',
    'EKCH_A_TWR', 'ekch_a_twr',
    'EKCH_D_TWR', 'ekch_d_twr',
    'EKCH_C_TWR', 'ekch_c_twr',
    'EKRK_TWR', 'ekrk_twr',
    'EKRK_APP', 'ekrk_app',
    'EKBI_TWR', 'ekbi_twr',
    'EKYT_TWR', 'ekyt_twr',
    'EKKA_TWR', 'ekka_twr',
    'EKAH_TWR', 'ekah_twr',
    'EKCH_W_APP', 'ekch_w_app',
    'EKCH_F_APP', 'ekch_f_app',
    'EKCH_W_DEP', 'ekch_w_dep',
    'EKBI_APP', 'ekbi_app',
    'EKYT_APP', 'ekyt_app',
    'EKKA_APP', 'ekka_app',
    'EKAH_APP', 'ekah_app',
    'EKDK_B_CTR', 'ekdk_b_ctr',
    'EKDK_D_CTR', 'ekdk_d_ctr',
    'EKDK_V_CTR', 'ekdk_v_ctr',
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

# Environment variables
VATSCA_MEMBER_ROLE = int(os.getenv('VATSCA_MEMBER_ROLE'))
VATSIM_MEMBER_ROLE = int(os.getenv('VATSIM_MEMBER_ROLE'))
EVENTS_ROLE = int(os.getenv('EVENTS_ROLE'))
S1_ROLE = int(os.getenv('S1_ROLE'))
S2_ROLE = int(os.getenv('S2_ROLE'))
S3_ROLE = int(os.getenv('S3_ROLE'))
C1_ROLE = int(os.getenv('C1_ROLE'))

GUILD_ID = int(os.getenv('GUILD_ID'))

EVENTS_CHANNEL = int(os.getenv('EVENTS_CHANNEL'))
RULES_CHANNEL = int(os.getenv('RULES_CHANNEL'))
ROLES_CHANNEL = int(os.getenv('ROLES_CHANNEL'))

VTC_CHANNEL = int(os.getenv('VTC_CHANNEL'))
VTC_STAFFING_MSG = int(os.getenv('VTC_STAFFING_MSG'))

BOT_CHANNEL = int(os.getenv('BOT_CHANNEL'))

CHECK_MEMBERS_INTERVAL = int(os.getenv('CHECK_MEMBERS_INTERVAL', 86400))
POST_EVENTS_INTERVAL = int(os.getenv('POST_EVENTS_INTERVAL', 30))
GET_EVENTS_INTERVAL = int(os.getenv('GET_EVENTS_INTERVAL', 900))

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
