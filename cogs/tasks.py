import os
import re
import discord

from datetime import datetime
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from helpers.message import staff_roles
from helpers.members import get_division_members
from helpers.handler import Handler
from helpers.config import (
    VATSIM_MEMBER_ROLE, VATSIM_SUBDIVISION, CHECK_MEMBERS_INTERVAL, 
    VATSCA_MEMBER_ROLE, ROLE_REASONS, GUILD_ID, DEBUG, STAFFING_INTERVAL
)

load_dotenv('.env')


class TasksCog(commands.Cog):
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

        if DEBUG and not override:
            print("check_members skipped due to DEBUG ON. You can start manually with command instead.", flush=True)
            return

        print("check_members started at " + str(datetime.now().isoformat()), flush=True)

        guild = self.bot.get_guild(GUILD_ID)

        vatsca_member = discord.utils.get(guild.roles, id=VATSCA_MEMBER_ROLE)
        vatsim_member = discord.utils.get(guild.roles, id=VATSIM_MEMBER_ROLE)

        memberlist = await get_division_members()
            
        for user in guild.members:            
            try:
                user_cid = re.findall(r'\d+', str(user.nick)) or [None]
                cid = int(user_cid[0]) if user_cid[0] else None

                if not cid:
                    raise ValueError('No CID found in nickname.')

                should_have_vatsca = any(int(entry['id']) == cid and str(entry['subdivision']) == VATSIM_SUBDIVISION for entry in memberlist)

                if cid:
                    await self.update_user_roles(self, user, vatsca_member, vatsim_member, should_have_vatsca)

            except ValueError as e:
                if vatsca_member in user.roles:
                    await user.remove_roles(vatsca_member, reason=ROLE_REASONS['no_cid'])
            
            except Exception as e:
                print(e, flush=True)
                continue


        print("check_members finished at " + str(datetime.now().isoformat()), flush=True)

    async def update_user_roles(self, user, vatsca_member, vatsim_member, should_have_vatsca):
        if vatsim_member in user.roles:
            if should_have_vatsca and vatsca_member not in user.roles:
                await user.add_roles(vatsca_member, reason=ROLE_REASONS['vatsca_add'])
            elif not should_have_vatsca and vatsca_member in user.roles:
                await user.remove_roles(vatsca_member, reason=ROLE_REASONS['vatsca_remove'])
        elif vatsca_member in user.roles:
            await user.remove_roles(vatsca_member, reason=ROLE_REASONS['no_auth'])

    @tasks.loop(seconds=CHECK_MEMBERS_INTERVAL)
    async def check_members_loop(self):
        await self.check_members()
    
    @app_commands.command(name="checkusers", description="Refresh roles based on division membership.")
    @app_commands.checks.has_any_role(*staff_roles())
    async def user_check(self, interaction: discord.Integration):
        ctx = Handler.get_context(self.bot, interaction)
        await ctx.send("Member refresh in progress")
        await self.check_members(True)
        await ctx.send("Member refresh process finished")

    async def sync_commands(self, override=False):
        if DEBUG and not override:
            print("sync_commands skipped due to DEBUG ON. You can start manually with command instead.", flush=True)
            return
        
        print(f"sync_commands started at {datetime.now().isoformat()}", flush=True)

        guild = self.bot.get_guild(GUILD_ID)

        try:    
            if guild:
                await self.bot.tree.sync(guild=guild) # Sync commands to a specific guild for faster deployment
            else:
                await self.bot.tree.sync() # Sync global commands (might take up to 1 hour to reflect globally)
            
            print("sync_commands finished at " + str(datetime.now().isoformat()), flush=True)
        except discord.HTTPException as e:
            print(f"Failed to sync commands due to rate limiting: {e}")

        except Exception as e:
            print(f'Failed to sync commands with error - {e} - at - {datetime.now().isoformat()}', flush=True)

    @app_commands.command(name='sync', description='Sync slash commands **Only accessable to staff**')
    @app_commands.checks.has_any_role(*staff_roles())
    async def sync(self, interaction: discord.Interaction):
        ctx = Handler.get_context(self.bot, interaction)
        await ctx.send("Sync commands in progress")
        await self.sync_commands(True)
        await ctx.send("Sync commands process finished")
        
    @tasks.loop(seconds=STAFFING_INTERVAL)
    async def sync_commands_loop(self):
        await self.sync_commands()
        

async def setup(bot):
    await bot.add_cog(TasksCog(bot))