import os
import re
import discord

from discord import app_commands
from discord.ext import commands, tasks

from datetime import datetime

from helpers.handler import Handler
from helpers.config import config

class TasksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.handler = Handler()
        self.check_members_loop.start()
        self.sync_commands_loop.start()

    def cog_unload(self):
        self.check_members_loop.cancel()
        self.sync_commands_loop.cancel()

    async def check_members(self, override = False):
        """
        Checks guild members and updates roles based on stored membership data.
        """
        await self.bot.wait_until_ready()

        if config.DEBUG and not override:
            print("check_members skipped due to DEBUG ON. You can start manually with the command instead.", flush=True)
            return
        
        print(f"check_members started at {datetime.now().isoformat()}", flush=True)

        guild = self.bot.get_guild(config.GUILD_ID)
        if not guild:
            print(f"Guild with ID {config.GUILD_ID} not found.", flush=True)
            return
        
        vatsca_role = discord.utils.get(guild.roles, id=config.VATSCA_MEMBER_ROLE)
        vatsim_role = discord.utils.get(guild.roles, id=config.VATSIM_MEMBER_ROLE)

        if not vatsca_role or not vatsim_role:
            print("Roles not configured correctly.", flush=True)
            return
        
        division_members = await self.handler.get_division_members()
        member_map = {  int(member["id"]): member for member in division_members }

        for user in guild.members:
            await self.proccess_member(user, vatsca_role, vatsim_role, member_map)

        print(f"check_members finished at {datetime.now().isoformat()}", flush=True)

    async def proccess_member(self, user, vatsca_role, vatsim_role, member_map):
        """
        Processes a single member to determine role assignments.

        Args:
            user (discord.Member): The member to process.
            vatsca_role (discord.Role): The VATSCA role.
            vatsim_role (discord.Role): The VATSIM role.
            member_map (dict): A map of division member CIDs to their corresponding API data.
        """
        try:
            cid = await self.handler.get_cid(user)
            if not cid:
                raise ValueError("No CID found in member's nickname.")
            
            is_vatsca_member = cid in member_map and member_map[cid]["subdivision"] == config.VATSIM_SUBDIVISION

            if vatsim_role in user.roles:
                await self.update_role(user, vatsca_role, is_vatsca_member, config.ROLE_REASONS['vatsca_add'], config.ROLE_REASONS['vatsca_remove'])
            elif vatsca_role in user.roles:
                await user.remove_roles(vatsca_role, reason=config.ROLE_REASONS['no_auth'])

        except ValueError as e:
            if vatsca_role in user.roles:
                await user.remove_roles(vatsca_role, reason=config.ROLE_REASONS['no_cid'])
        
        except Exception as e:
            print(f"Error processing member {user}: {e}", flush=True)

    async def update_role(self, user, role, should_have_role, add_reason, remove_reason):
        """
        Adds or removes a role based on conditions.
        """
        if should_have_role and role not in user.roles:
            await user.add_roles(role, reason=add_reason)
        elif not should_have_role and role in user.roles:
            await user.remove_roles(role, reason=remove_reason)
    
    @tasks.loop(seconds=config.CHECK_MEMBERS_INTERVAL)
    async def check_members_loop(self):
        await self.check_members()

    @app_commands.command(name="checkusers", description="Refresh roles based on division membership.")
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def checkusers(self, interaction: discord.Interaction):
        ctx = await self.handler.get_context(self.bot, interaction)
        await ctx.send("Member refresh in progress.", ephemeral=True)
        await self.check_members(override=True)
        await ctx.send("Member refresh completed.", ephemeral=True)

    async def sync_commands(self, override = False):
        """
        Syncs slash commands with Discord servers.
        """
        if config.DEBUG and not override:
            print("sync_commands skipped due to DEBUG ON. You can start manually with the command instead.", flush=True)
            return
        
        guild = self.bot.get_guild(config.GUILD_ID)
        try:
            print(f"sync_commands started at {datetime.now().isoformat()}", flush=True)
            await self.bot.tree.sync(guild=guild) if guild else await self.bot.tree.sync()
            print(f"sync_commands finished at {datetime.now().isoformat()}", flush=True)
        
        except Exception as e:
            print(f"Failed to sync commands: {e}", flush=True)

    @app_commands.command(name="sync", description="Sync slash commands (Staff only).")
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def sync(self, interaction: discord.Interaction):
        ctx = await self.handler.get_context(self.bot, interaction)
        await ctx.send("Slash command sync in progress.", ephemeral=True)
        await self.sync_commands(override=True)
        await ctx.send("Slash command sync completed.", ephemeral=True)

    @tasks.loop(seconds=config.STAFFING_INTERVAL)
    async def sync_commands_loop(self):
        await self.sync_commands()

async def setup(bot):
    await bot.add_cog(TasksCog(bot))