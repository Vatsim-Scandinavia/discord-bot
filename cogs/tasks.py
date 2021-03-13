import os
import re

import discord
import mysql.connector
import requests
from discord.ext import commands, tasks
from discord_slash import cog_ext, SlashContext
from dotenv import load_dotenv
from helpers.message import roles

from helpers.config import VATSIM_MEMBER_ROLE, CHECK_MEMBERS_INTERVAL, VATSCA_MEMBER_ROLE, ROLE_REASONS, GUILD_ID

load_dotenv('.env')


class TasksCog(commands.Cog):
    VATSCA_ROLE_ADD_REASON = ROLE_REASONS['vatsca_add']
    VATSCA_ROLE_REMOVE_REASON = ROLE_REASONS['vatsca_remove']
    NO_CID_REMOVE_REASON = ROLE_REASONS['no_cid']
    NO_AUTH_REMOVE_REASON = ROLE_REASONS['no_auth']

    def __init__(self, bot):
        self.bot = bot
        self.check_members_loop.start()

    def cog_unload(self):
        self.check_members_loop.cancel()

    async def check_members(self):
        """
        Task checks guild members and assigns roles according to the data we've stored in our system
        :return:
        """
        guild = self.bot.get_guild(GUILD_ID)
        users = guild.members

        vatsca_member = discord.utils.get(guild.roles, id=VATSCA_MEMBER_ROLE)
        vatsim_member = discord.utils.get(guild.roles, name=VATSIM_MEMBER_ROLE)

        for user in users:
            if vatsim_member not in user.roles:
                if vatsca_member in user.roles:
                    await user.remove_roles(vatsca_member, reason=self.NO_AUTH_REMOVE_REASON)
                continue

            try:

                cid = re.findall('\d+', str(user.nick))

                if len(cid) < 1:
                    raise ValueError

                statement = "https://api.vatsim.net/api/ratings/" + str(cid[0])
                request = requests.get(statement)
                if request.status_code == requests.codes.ok:
                    request = request.json()
                else:
                    continue


                if vatsca_member not in user.roles and request["subdivision"] == 'SCA':
                    await user.add_roles(vatsca_member, reason=self.VATSCA_ROLE_ADD_REASON)
                elif vatsca_member in user.roles and request["subdivision"] != 'SCA':
                    await user.remove_roles(vatsca_member, reason=self.VATSCA_ROLE_REMOVE_REASON)

            except ValueError as e:
                if vatsca_member in user.roles:
                    await user.remove_roles(vatsca_member, reason=self.NO_CID_REMOVE_REASON)
                """if vatsim_member in user.roles:
                    await user.remove_roles(vatsim_member, reason=self.NO_CID_REMOVE_REASON)"""

            except Exception as e:
                print(e)
                continue

    @tasks.loop(seconds=CHECK_MEMBERS_INTERVAL)
    async def check_members_loop(self):
        await self.check_members()

    guild_ids = [GUILD_ID]
    
    @cog_ext.cog_slash(name="usercheck", guild_ids=guild_ids, description="Bot manually check members.")
    @commands.has_any_role(*roles())
    async def user_check(self, ctx):
        await self.check_members()
        await ctx.send("Checking members!")


def setup(bot):
    bot.add_cog(TasksCog(bot))