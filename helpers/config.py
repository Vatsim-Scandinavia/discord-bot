import discord
import os
from dotenv import load_dotenv
from distutils.util import strtobool

import discord.ext

load_dotenv('.env')

class Config:
    def __init__(self):
        """
        Environment Variables
        """
        
        # Essential variables
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        self.GUILD_ID = int(os.getenv('GUILD_ID', 0))
        self.DEBUG = bool(strtobool(os.getenv('DEBUG', 'False')))

        self.PREFIX = "/"
        self.VATSCA_BLUE = 0x43c6e7

        self.DESCRIPTION = 'This is a new VATSCA Discord Bot'
        self.PRESENCE_TEXT = "VATSCA Airspace"

        # Cogs and admin roles
        self.COGS = [
            'cogs.admin',
            'cogs.member',
            'cogs.roles',
            'cogs.tasks',
            'cogs.update_messages',
            'cogs.staffings',
        ]

        self.COGS_LOAD = {
            'admin': 'cogs.admin',
            'member': 'cogs.member',
            'roles': 'cogs.roles',
            'tasks': 'cogs.tasks',
            'update_messages': 'cogs.update_messages',
            'staffings': 'cogs.staffings',
        }

        self.STAFF_ROLES = [
            'Web',
            'Discord Moderator',
            'Discord Administrator',
            'Board',
            'Staff',
        ]

        self.ROLE_REASONS = {
            'vatsca_add': 'Member is now part of VATSCA',
            'vatsca_remove': 'Member is no longer part of VATSCA',
            'no_cid': 'User does not have a VATSIM ID in his/her nickname.',
            'no_auth': 'User did not authenticate via the Community Website',
            'mentor_add': 'Member is now a mentor',
            'mentor_remove': 'Member is no longer a mentor',
            'examiner_add': 'Member is now an examiner',
            'examiner_remove': 'Member is no longer an examiner',
            'training_add': 'Member is now in training',
            'training_remove': 'Member is no longer in training',
            'training_staff_add': 'Member is now Traning Staff',
            'training_staff_remove': 'Member is no longer Training Staff',
            'visitor_add': 'Member is now Visiting Controller',
            'visitor_remove': 'Member is no longer Visiting Controller',
            'reaction_add': 'Member reacted to a message',
            'reaction_remove': 'Member removed a reaction from a message',
        }

        # VATSIM API
        self.VATSIM_API_TOKEN = str(os.getenv("VATSIM_API_TOKEN", ""))
        self.VATSIM_CHECK_MEMBER_URL = str(os.getenv("VATSIM_CHECK_MEMBER_URL", ""))
        self.VATSIM_SUBDIVISION = str(os.getenv("VATSIM_SUBDIVISION", ""))
        self.DIVISION_URL = str(os.getenv("DIVISION_URL", ""))

        # CC API
        self.CC_API_URL = str(os.getenv('CC_API_URL', ''))
        self.CC_API_TOKEN = str(os.getenv('CC_API_TOKEN', ''))

        # Event Calendar API
        self.EVENT_CALENDAR_URL = str(os.getenv('EVENT_CALENDAR_URL', ''))
        self.EVENT_API_TOKEN = str(os.getenv('EVENT_API_TOKEN', ''))
        self.EVENT_CALENDAR_TYPE = int(os.getenv('EVENT_CALENDAR_TYPE', ''))

        # Adjacent API keys
        self.SENTRY_KEY = str(os.getenv("SENTRY_KEY"))

        self.METAR_API_KEY = str(os.getenv("METAR_API_KEY", ""))

        # Role IDs
        self.VATSCA_MEMBER_ROLE = int(os.getenv("VATSCA_MEMBER_ROLE", 0))
        self.VATSIM_MEMBER_ROLE = int(os.getenv("VATSIM_MEMBER_ROLE", 0))
        self.EVENTS_ROLE = int(os.getenv("EVENTS_ROLE", 0))
        self.MENTOR_ROLE = int(os.getenv("MENTOR_ROLE", 0))
        self.TRAINING_STAFF_ROLE = int(os.getenv("TRAINING_STAFF_ROLE", 0))
        self.VISITOR_ROLE = int(os.getenv("VISITOR_ROLE", 0))
        self.OBS_ROLE = int(os.getenv("OBS_ROLE", 0))

        # FIR Data
        self.FIR_DATA = [ fir.split(':') for fir in os.getenv('FIR_DATA', '').split(',') if fir]
        self.FIRS, self.FIR_ROLES = zip(*self.FIR_DATA) if self.FIR_DATA else ([], [])
        self.FIR_MENTORS = dict(zip(self.FIRS, self.FIR_ROLES))

        # Examiner Data (same format as FIR data)
        self.EXAMINER_DATA = [ fir.split(':') for fir in os.getenv('EXAMINER_DATA', '').split(',') if fir]
        self.EXAM_FIRS, self.EXAM_ROLES = zip(*self.EXAMINER_DATA) if self.EXAMINER_DATA else ([], [])
        self.FIR_EXAMINERS = dict(zip(self.EXAM_FIRS, self.EXAM_ROLES))

        # Training Data
        self.TRAINING_DATA = os.getenv('TRAINING_DATA', '').split(',')
        self.TRAINING_ROLES = {
            country: {role.split(':')[0]: role.split(':')[1] for role in roles_str.split(',')}
            for country, roles_str in (entry.split('|') for entry in self.TRAINING_DATA if '|' in entry)
        }

        self.CONTROLLER_FIR_DATA = [ fir.split(':') for fir in os.getenv('CONTROLLER_FIR_DATA', '').split(',') if fir]
        self.CONTROLLER_FIRS, self.CONTROLLER_ROLES = zip(*self.CONTROLLER_FIR_DATA) if self.CONTROLLER_FIR_DATA else ([], [])
        self.CONTROLLER_FIR_ROLES = dict(zip(self.CONTROLLER_FIRS, self.CONTROLLER_ROLES))

        # Parse RATING_FIR_DATA from the environment variable
        self.RATING_FIR_DATA_RAW = os.getenv('RATING_FIR_DATA', '')
        self.RATING_FIR_DATA = {}
        if self.RATING_FIR_DATA_RAW:
            fir_entries = self.RATING_FIR_DATA_RAW.split('|')
            fir_name = fir_entries[0].strip()
            ratings = {}

            for rating_entry in fir_entries[1:]:
                rating, role_id = rating_entry.split(':')
                ratings[rating.strip()] = int(role_id.strip())

            self.RATING_FIR_DATA[fir_name] = ratings

        self.c1_equivalent_ratings = {"ADM", "SUP", "C1", "C2", "C3", "I1", "I3"}

        # Parse REACTION_ROLE_DATA from the environment variable
        self.REACTION_ROLE_DATA = os.getenv('REACTION_ROLE_DATA', '')
        self.REACTION_EMOJI, self.REACTION_MESSAGE_IDS, self.REACTION_ROLE_IDS = [], [], []

        if self.REACTION_ROLE_DATA:
            for reaction_role in self.REACTION_ROLE_DATA.split(','):
                emoji, message_id, role_id = reaction_role.split('|')
                self.REACTION_EMOJI.append(emoji)
                self.REACTION_MESSAGE_IDS.append(message_id)
                self.REACTION_ROLE_IDS.append(role_id)

        self.REACTION_ROLES = dict(zip(self.REACTION_EMOJI, self.REACTION_ROLE_IDS))

        # Intervals
        self.CHECK_MEMBERS_INTERVAL = int(os.getenv('CHECK_MEMBERS_INTERVAL', 86400))
        self.STAFFING_INTERVAL = int(os.getenv('STAFFING_INTERVAL', 0))

        # Channel IDs
        self.EVENTS_CHANNEL = int(os.getenv('EVENTS_CHANNEL', 0))
        self.RULES_CHANNEL = int(os.getenv('RULES_CHANNEL', 0))
        self.WELCOME_CHANNEL = int(os.getenv('WELCOME_CHANNEL', 0))
        self.ROLES_CHANNEL = int(os.getenv('ROLES_CHANNEL', 0))

        # Database variables
        self.BOT_DB_HOST = str(os.getenv('BOT_DB_HOST', ''))
        self.BOT_DB_PORT = str(os.getenv('BOT_DB_PORT', ''))
        self.BOT_DB_USER = str(os.getenv('BOT_DB_USER', ''))
        self.BOT_DB_PASSWORD = str(os.getenv('BOT_DB_PASSWORD', ''))
        self.BOT_DB_NAME = str(os.getenv('BOT_DB_NAME', ''))

    def activity(self) -> discord.Activity:
        return discord.Activity(type=discord.ActivityType.watching, name=self.PRESENCE_TEXT)
    
    def status(self) -> discord.Status:
        return discord.Status.online
    
    async def load_cogs(self, bot: discord.ext.commands.Bot) -> None:
        for cog in self.COGS:
            try:
                await bot.load_extension(cog)
            except Exception as e:
                print(f'Failed to load cog - {cog}. \n Error: {e}', flush=True)
            

config = Config()