from discord.ext import commands, tasks
import discord
from helpers.config import VATSIM_MEMBER_ROLE, CHECK_MEMBERS_INTERVAL, VATSCA_MEMBER_ROLE
import re
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv('.env')

class TasksCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.checkMembers.start()

    def cog_unload(self):
        self.checkMembers.cancel()

    @tasks.loop(seconds=CHECK_MEMBERS_INTERVAL)
    async def checkMembers(self):
        guild = self.bot.get_guild(776110954437148672)
        users = guild.members
        mydb = mysql.connector.connect(
            host="localhost",
            user=os.getenv('USER'),
            password=os.getenv('PASSWORD'),
            database=os.getenv('DATABASE')
        )

        cursor = mydb.cursor()

        for user in users:
            if discord.utils.get(guild.roles, name=VATSIM_MEMBER_ROLE) not in user.roles:
                continue

            cid = re.findall('\d+', user.nick)

            try:
            
                statment = "SELECT subdivision FROM users WHERE id = %s"

                cursor.execute(statment, cid)

                result = cursor.fetchone()

                role = discord.utils.get(guild.roles, id=VATSCA_MEMBER_ROLE)

                if role not in user.roles and result[0] == 'SCA':
                    await user.add_roles(role, reason='Member is now part of VATSCA')
                elif role in user.roles and result[0] != 'SCA':
                    await user.remove_roles(role, reason='Member is no longer part of VATSCA')

            except:
                continue

        mydb.close()

def setup(bot):
    bot.add_cog(TasksCog(bot))