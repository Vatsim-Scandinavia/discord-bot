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
        ]

        self.COGS_LOAD = {
            'admin': 'cogs.admin',
            'member': 'cogs.member',
        }

        self.STAFF_ROLES = [
            'Web',
            'Discord Moderator',
            'Discord Administrator',
            'Board',
            'Staff',
        ]

        # VATSIM API
        self.VATSIM_API_TOKEN = str(os.getenv("VATSIM_API_TOKEN", ""))
        self.VATSIM_CHECK_MEMBER_URL = str(os.getenv("VATSIM_CHECK_MEMBER_URL", ""))
        self.VATSIM_SUBDIVISION = str(os.getenv("VATSIM_SUBDIVISION", ""))
        self.DIVISION_URL = str(os.getenv("DIVISION_URL", ""))

        # Adjacent API keys
        self.SENTRY_KEY = str(os.getenv("SENTRY_KEY"))

        self.METAR_API_KEY = str(os.getenv("METAR_API_KEY", ""))

        # Role IDs
        self.VATSCA_MEMBER_ROLE = int(os.getenv("VATSCA_MEMBER_ROLE", 0))
        self.VATSIM_MEMBER_ROLE = int(os.getenv("VATSIM_MEMBER_ROLE", 0))

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