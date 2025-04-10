import asyncio
import datetime
import logging
from collections.abc import Coroutine
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

from helpers.config import config
from helpers.handler import Handler
from helpers.member_cache import MemberCache

logger = logging.getLogger(__name__)

VATSIM_BASE_URL = 'https://data.vatsim.net'
VATSIM_DATA = '/v3/vatsim-data.json'


class VATSIMDataFetchException(Exception):
    """Custom exception for VATSIM data fetch errors."""

    status_code: int

    def __init__(self, response: aiohttp.ClientResponse):
        self.status_code = response.status
        super().__init__(f'Failed to fetch VATSIM data: HTTP {self.status_code}')


class CoordinationCog(commands.Cog):
    """
    A cog for exposing VATSIM controller status in Discord voice channels.
    This cog handles the synchronization between VATSIM controller status and Discord voice channel
    member nicknames. It periodically fetches online controller data from VATSIM and updates
    Discord member nicknames to reflect their controlling status when they join/leave voice channels.

    Commands:
        updatevoice: Manually trigger nickname updates for all voice channel members

    Events:
        on_voice_state_update: Handles nickname updates when members join/leave voice channels

    Tasks:
        update_controllers_cache: Periodic task to refresh online controller data

    Note:
        Requires appropriate Discord permissions to modify member nicknames
        Relies on VATSIM Datafeed API for controller status data

    """

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._handler = Handler()
        self._last_update: datetime.datetime = None
        self._session = aiohttp.ClientSession(base_url=VATSIM_BASE_URL)
        self._online_controllers: dict[str, str] = {}
        self._member_cache = MemberCache(folder=config.CACHE_DIR)
        self._update_controllers_cache.start()
        # TODO(thor): remove this allow list after validation
        self._allowed_cids = config.COORDINATION_ALLOWED_CIDS
        logger.info('Initialized and started updating controllers cache')

    async def cog_unload(self):
        self._update_controllers_cache.cancel()
        await self._session.close()
        await self._clean_up()
        logger.info('Stopped updating cache and attempted restoring existing members')

    async def _clean_up(self):
        ids = self._member_cache.get_member_ids()
        members = self._bot.get_all_members()
        tasks = [
            self._update_member_nickname(member=member, force_remove=True)
            for member in members
            if member.id in ids
        ]
        _create_task(*tasks)

    async def _fetch_online_controllers(self) -> dict[int, str]:
        """Fetch online controllers from VATSIM Datafeed API"""
        try:
            async with self._session.get(VATSIM_DATA) as response:
                if response.status != 200:
                    raise VATSIMDataFetchException(response)
                data = await response.json()
            controllers = {}
            for controller in data.get('controllers', []):
                if controller.get('facility') != 0:
                    cid = int(controller.get('cid'))
                    controllers[cid] = controller.get('callsign')
            return controllers
        except VATSIMDataFetchException:
            raise
        except Exception:
            logger.exception('Failed to fetch online controllers')
            return {}

    @tasks.loop(minutes=1, reconnect=True)
    async def _update_controllers_cache(self):
        """Update the cache of online controllers periodically"""
        try:
            logger.debug('Updating online controllers cache...')
            self._online_controllers = await self._fetch_online_controllers()
            self._last_update = datetime.datetime.now()
            # TODO(thor): consider splitting into a separate background task
            await self._update_voice_channel_members()
        except Exception as e:
            logger.exception(f'Failed to update controllers cache: {e}')

    async def _get_controller_station(self, cid: int) -> Optional[str]:
        """Get the controller's prefix if they're online, None otherwise"""
        if cid in self._online_controllers:
            return self._online_controllers[cid].replace('__', '_')
        return None

    async def _restore_nickname(self, member: discord.Member) -> None:
        """Restore the original nickname of a member"""
        original_nick = self._member_cache.get_nickname(member.id)
        if not original_nick:
            logger.warning('Original nickname not found', extra={member: member})
            return

        # Remove the nickname first to avoid issue for those weird users who have higher permissions
        # than the bot itself. This is an additional risk, but one we're fine to make.
        _create_task(self._member_cache.remove_nickname(member.id))
        await member.edit(
            nick=original_nick,
            reason='Removing callsign prefix after leaving voice channel',
        )

    def _format_name(self, prefix: str, name: str, cid: int) -> str:
        return f'{prefix}: {name} - {cid}'

    async def _update_member_nickname(
        self, member: discord.Member, force_remove: bool = False
    ) -> None:
        """Update member's nickname based on their controlling station"""
        try:
            if not member.voice or force_remove:
                await self._restore_nickname(member)
                return

            cid = await self._handler.get_cid(member)
            name = self._handler.get_name(member)
            if not cid or not name:
                return

            # TODO(thor): remove after validation
            if cid not in self._allowed_cids:
                logger.info(f"Skipping CID {cid} as it's not in {self._allowed_cids}")
                return

            current_nick = member.nick or member.name
            prefix = await self._get_controller_station(cid)
            if not prefix and ':' in current_nick:
                await self._restore_nickname(member)
                return

            # Add the prefix to the user and and store original nickname before modification
            _create_task(self._member_cache.store_nickname(member.id, current_nick))
            new_name_candidate = self._format_name(prefix, name, cid)
            max_length = max(0, len(name) - (len(new_name_candidate) - 32))
            short_name = _ellipsify(name, max_length)
            new_name = self._format_name(prefix, short_name, cid)
            await member.edit(
                nick=new_name[:32],
                reason='Adding callsign prefix after joining voice channel',
            )
            logger.info(f'Updating nickname for {member} to {new_name=}')

        except discord.Forbidden:
            logger.warning(f'Bot lacks permission to change nickname of {member}')
        except Exception as e:
            logger.exception(f'Error updating nickname for {member}: {e}')

    async def _update_voice_channel_members(self):
        """Update all members in voice channels across all guilds"""
        tasks = []
        for guild in self._bot.guilds:
            for channel in guild.voice_channels:
                tasks.extend(
                    [self._update_member_nickname(member) for member in channel.members]
                )
        await asyncio.gather(*tasks)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        """Handle voice state changes to update nicknames"""
        if before.channel == after.channel:
            return

        if after.channel is None:
            # User left voice voice channels altogether
            await self._update_member_nickname(member, force_remove=True)
        else:
            # The user moved to a different voice channel
            await self._update_member_nickname(member)

    @app_commands.command(
        name='updatevoice', description='Update voice channel member nicknames'
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def update_voice(self, interaction: discord.Interaction):
        """Manually update all voice channel member nicknames"""
        try:
            await interaction.response.defer(ephemeral=True)
            await self._update_voice_channel_members()
            await interaction.followup.send(
                'Voice channel nicknames updated.', ephemeral=True
            )
        except Exception as e:
            logger.exception(f'Error in update_voice command: {e}')
            await interaction.followup.send(
                'An error occurred while updating nicknames.', ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(CoordinationCog(bot))


_background_tasks = set()


def _create_task(*coroutines: Coroutine):
    """Decorator to run a function in the background without waiting for it to finish"""
    for coroutine in coroutines:
        task = asyncio.create_task(coroutine)
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)


def _ellipsify(needle: str, max_length: int) -> str:
    """Shorten needle to fit within max_length characters"""
    if len(needle) > max_length:
        shortened = needle[: max_length - 1]
        # Remove trailing space if present
        if shortened[-1].isspace():
            shortened = shortened[:-1]
        return shortened + '…'
    return needle
