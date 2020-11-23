from discord.ext import commands, tasks
import discord
from helpers.config import VATSIM_MEMBER_ROLE, CHECK_MEMBERS_INTERVAL, VATSCA_MEMBER_ROLE, ROLE_REASONS
import re
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv('.env')


class TasksCog(commands.Cog):

    VATSCA_ROLE_ADD_REASON = ROLE_REASONS['vatsca_add']
    VATSCA_ROLE_REMOVE_REASON = ROLE_REASONS['vatsca_remove']
    NO_CID_REMOVE_REASON = ROLE_REASONS['no_cid']

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.checkMembers.start()

    def cog_unload(self):
        self.checkMembers.cancel()

    @tasks.loop(seconds=5)
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
                    await user.remove_roles(vatsca_member, reason='User did not authenticate via the Community Website')
                continue

            try:

                cid = re.findall('\d+', user.nick)

                if len(cid) < 1:
                    raise ValueError

                statement = "SELECT subdivision FROM users WHERE id = %s"

                cursor.execute(statement, cid)

                result = cursor.fetchone()

                if vatsca_member not in user.roles and result[0] == 'SCA':
                    await user.add_roles(vatsca_member, reason=self.VATSCA_ROLE_ADD_REASON)
                elif vatsca_member in user.roles and result[0] != 'SCA':
                    await user.remove_roles(vatsca_member, reason=self.VATSCA_ROLE_REMOVE_REASON)

            except ValueError as e:
                if vatsca_member in user.roles:
                    await user.remove_roles(vatsca_member, reason=self.NO_CID_REMOVE_REASON)

            except Exception as e:
                print(e)
                continue

        mydb.close()


def setup(bot):
    bot.add_cog(TasksCog(bot))
