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

        vatsca_member = discord.utils.get(guild.roles, id=VATSCA_MEMBER_ROLE)
        vatsim_member = discord.utils.get(guild.roles, name=VATSIM_MEMBER_ROLE)

        for user in users:
            if vatsim_member not in user.roles:
                if vatsca_member in user.roles:
                    await user.remove_roles(vatsca_member)

                continue


            try:

                cid = re.findall('\d+', user.nick)

                if len(cid) < 1:
                    raise ValueError
            
                statment = "SELECT subdivision FROM users WHERE id = %s"

                cursor.execute(statment, cid[0])

                result = cursor.fetchone()

                if vatsca_member not in user.roles and result[0] == 'SCA':
                    await user.add_roles(vatsca_member, reason='Member is now part of VATSCA')
                elif vatsca_member in user.roles and result[0] != 'SCA':
                    await user.remove_roles(vatsca_member, reason='Member is no longer part of VATSCA')

            except ValueError as e:
                if vatsca_member in user.roles:
                    await user.remove_roles(vatsca_member)

            except Exception as e:
                continue

        mydb.close()

def setup(bot):
    bot.add_cog(TasksCog(bot))