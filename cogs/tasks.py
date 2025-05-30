from datetime import datetime

import discord
import structlog
from discord import app_commands
from discord.ext import commands, tasks

from helpers.config import config
from helpers.handler import Handler
from helpers.ux import NicknameAssignment

logger = structlog.stdlib.get_logger()


class TasksCog(commands.Cog):
    maintenance = app_commands.Group(
        name='maintenance',
        description='Maintenance commands for the bot.',
    )

    def __init__(self, bot):
        self.bot = bot
        self.handler = Handler()
        self.check_members_loop.start()
        self.sync_commands_loop.start()

    async def cog_unload(self):
        self.check_members_loop.cancel()
        self.sync_commands_loop.cancel()

    async def check_members(self, override=False):
        """Checks guild members and updates roles based on stored membership data."""
        await self.bot.wait_until_ready()

        if config.DEBUG and not override:
            logger.info(
                'check_members skipped due to DEBUG ON. You can start it manually with the command instead.'
            )
            return

        logger.info(
            'check_members started',
            start_time=datetime.now().isoformat(),
            status='started',
        )

        guild = self.bot.get_guild(config.GUILD_ID)
        if not guild:
            logger.error('Guild not found', guild_id=config.GUILD_ID)
            return

        vatsca_role = discord.utils.get(guild.roles, id=config.VATSCA_MEMBER_ROLE)
        vatsim_role = discord.utils.get(guild.roles, id=config.VATSIM_MEMBER_ROLE)

        if not vatsca_role or not vatsim_role:
            logger.error(
                'Roles not configured correctly',
                division_role=vatsca_role,
                vatsim_role=vatsim_role,
            )
            return

        division_members = await self.handler.get_division_members()
        member_map = {int(member['id']): member for member in division_members}
        logger.info('Fetched division members in check_members', len=len(member_map))

        for user in guild.members:
            await self.proccess_member(user, vatsca_role, vatsim_role, member_map)

        logger.info(
            'check_members finished',
            end_time=datetime.now().isoformat(),
            status='success',
        )

    async def proccess_member(self, user, vatsca_role, vatsim_role, member_map):
        """
        Processes a single member to determine role assignments.

        Args:
            user (discord.Member): The member to process.
            vatsca_role (discord.Role): The VATSCA role.
            vatsim_role (discord.Role): The VATSIM role.
            member_map (dict): A map of division member CIDs to their corresponding API data.

        Todo:
            Replace `vatsca_role` with `subdivision_role`.

        """
        try:
            cid = self.handler.get_cid(user)
            if not cid:
                raise ValueError("No CID found in member's nickname.")

            is_vatsca_member = (
                cid in member_map
                and member_map[cid]['subdivision'] == config.VATSIM_SUBDIVISION
            )

            if vatsim_role in user.roles:
                await self.update_role(
                    user,
                    vatsca_role,
                    is_vatsca_member,
                    config.ROLE_REASONS['vatsca_add'],
                    config.ROLE_REASONS['vatsca_remove'],
                )
            elif vatsca_role in user.roles:
                await user.remove_roles(
                    vatsca_role, reason=config.ROLE_REASONS['no_auth']
                )

        # TODO(thor): use a specific exception, or return null rather than throw a generic ValueError
        except ValueError:
            if vatsca_role in user.roles:
                await user.remove_roles(
                    vatsca_role, reason=config.ROLE_REASONS['no_cid']
                )

        except Exception as e:
            logger.exception('Error processing member', member=user, error=str(e))

    async def update_role(
        self, user, role, should_have_role, add_reason, remove_reason
    ):
        """Adds or removes a role based on conditions."""
        if should_have_role and role not in user.roles:
            await user.add_roles(role, reason=add_reason)
        elif not should_have_role and role in user.roles:
            await user.remove_roles(role, reason=remove_reason)

    @tasks.loop(seconds=config.CHECK_MEMBERS_INTERVAL)
    async def check_members_loop(self):
        await self.check_members()

    @app_commands.command(
        name='checkusers', description='Refresh roles based on division membership.'
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def checkusers(self, interaction: discord.Interaction):
        ctx = await self.handler.get_context(self.bot, interaction)
        await ctx.send('Member refresh in progress.', ephemeral=True)
        await self.check_members(override=True)
        await ctx.send('Member refresh completed.', ephemeral=True)

    async def sync_commands(self, override=False):
        """Syncs slash commands with Discord servers."""
        if config.DEBUG and not override:
            logger.info(
                'Skipped job due to DEBUG mode. You can start the job with the command.',
                job='sync_commands',
                status='skipped',
            )
            return

        guild = self.bot.get_guild(config.GUILD_ID)
        try:
            logger.info(
                'Job started',
                job='sync_commands',
                start_time=datetime.now().isoformat(),
                status='started',
            )
            (
                await self.bot.tree.sync(guild=guild)
                if guild
                else await self.bot.tree.sync()
            )
            logger.info(
                'Job finished',
                job='sync_commands',
                end_time=datetime.now().isoformat(),
                status='finished',
            )

        except Exception as e:
            logger.exception(
                'Failed synchronisation of commands due to unexpected exception',
                job='sync_commands',
                error=e,
            )

    @app_commands.command(name='sync', description='Sync slash commands (Staff only).')
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def sync(self, interaction: discord.Interaction):
        ctx = await self.handler.get_context(self.bot, interaction)
        await ctx.send('Slash command sync in progress.', ephemeral=True)
        await self.sync_commands(override=True)
        await ctx.send('Slash command sync completed.', ephemeral=True)

    @maintenance.command(name='nick', description='Manually override a member nickname')
    @app_commands.describe(member='Member to update')
    @app_commands.checks.has_any_role(*config.TECH_ROLES)
    async def set_nick(self, interaction: discord.Interaction, member: discord.Member):
        """Manually override a member nickname to fix problems"""
        try:
            await interaction.response.send_modal(NicknameAssignment(member=member))
        except Exception:
            await interaction.followup.send(
                'An error occurred while setting the nick.', ephemeral=True
            )

    @tasks.loop(seconds=config.STAFFING_INTERVAL)
    async def sync_commands_loop(self):
        await self.sync_commands()


async def setup(bot):
    await bot.add_cog(TasksCog(bot))
