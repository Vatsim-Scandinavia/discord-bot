import os
import re

import discord
import requests

from datetime import datetime
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from helpers.message import staff_roles
from helpers.members import get_division_members

from helpers.config import VATSIM_MEMBER_ROLE, VATSIM_SUBDIVISION, CHECK_MEMBERS_INTERVAL, VATSCA_MEMBER_ROLE, ROLE_REASONS, GUILD_ID, DEBUG, STAFFING_INTERVAL

load_dotenv('.env')


class TasksCog(commands.Cog):
    VATSCA_ROLE_ADD_REASON = ROLE_REASONS['vatsca_add']
    VATSCA_ROLE_REMOVE_REASON = ROLE_REASONS['vatsca_remove']
    NO_CID_REMOVE_REASON = ROLE_REASONS['no_cid']
    NO_AUTH_REMOVE_REASON = ROLE_REASONS['no_auth']

    def __init__(self, bot):
        self.bot = bot
        self.check_members_loop.start()
        self.sync_commands_loop.start()

    def cog_unload(self):
        self.check_members_loop.cancel()
        self.sync_commands_loop.start()

    async def check_members(self, override=False):
        """
        Task checks guild members and assigns roles according to the data we've stored in our system
        :return:
        """

        await self.bot.wait_until_ready()

        if DEBUG == True and override == False:
            print("check_members skipped due to DEBUG ON. You can start manually with command instead.")
            return

        print("check_members started at " + str(datetime.now().isoformat()))

        guild = self.bot.get_guild(GUILD_ID)
        users = guild.members

        vatsca_member = discord.utils.get(guild.roles, id=VATSCA_MEMBER_ROLE)
        vatsim_member = discord.utils.get(guild.roles, id=VATSIM_MEMBER_ROLE)

        memberlist = await get_division_members()
            
        for user in users:            
            try:
                cid = re.findall('\d+', str(user.nick))

                if len(cid) < 1:
                    raise ValueError

                should_have_vatsca = False

                for entry in memberlist:
                    if int(entry['id']) == int(cid[0]) and str(entry["subdivision"]) == str(VATSIM_SUBDIVISION):
                        should_have_vatsca = True

                if vatsim_member in user.roles:
                    if vatsca_member not in user.roles and should_have_vatsca == True:
                        await user.add_roles(vatsca_member, reason=self.VATSCA_ROLE_ADD_REASON)
                    elif vatsca_member in user.roles and should_have_vatsca == False:
                        await user.remove_roles(vatsca_member, reason=self.VATSCA_ROLE_REMOVE_REASON)
                elif vatsim_member not in user.roles and vatsca_member in user.roles:
                    await user.remove_roles(vatsca_member, reason=self.NO_AUTH_REMOVE_REASON)

            except ValueError as e:
                if vatsca_member in user.roles:
                    await user.remove_roles(vatsca_member, reason=self.NO_CID_REMOVE_REASON)
            except Exception as e:
                print(e)
                continue


        print("check_members finished at " + str(datetime.now().isoformat()))


    @tasks.loop(seconds=CHECK_MEMBERS_INTERVAL)
    async def check_members_loop(self):
        await self.check_members()
    
    @app_commands.command(name="checkusers", description="Refresh roles based on division membership.")
    @commands.has_any_role(*staff_roles())
    async def user_check(self, interaction: discord.Integration):
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx 
        await ctx.send("Member refresh in progress")
        await self.check_members(True)
        await ctx.send("Member refresh process finished")

    async def sync_commands(self, override=False):
        now = datetime.now().isoformat()
        try:
            if DEBUG == True and override == False:
                print("sync_commands skipped due to DEBUG ON. You can start manually with command instead.")
                return
            print("sync_commands started at " + str(datetime.now().isoformat()))
            await self.bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            print("sync_commands finished at " + str(datetime.now().isoformat()))
        except Exception as e:
            print(f'Failed to sync commands with error - {e} - at - {now}')

    @app_commands.command(name='sync', description='Sync slash commands **Only accessable to staff**')
    @commands.has_any_role(*staff_roles())
    async def sync(self, interaction: discord.Interaction):
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx
        await ctx.send("Sync commands in progress")
        await self.sync_commands(True)
        await ctx.send("Sync commands process finished")
        
    @tasks.loop(seconds=STAFFING_INTERVAL)
    async def sync_commands_loop(self):
        await self.sync_commands()
        


async def setup(bot):
    await bot.add_cog(TasksCog(bot))