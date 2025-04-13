import asyncio
import datetime
import logging
from collections.abc import Coroutine
import re
from typing import Optional

import aiohttp
import discord
from discord import Member, app_commands
from discord.ext import commands, tasks

from helpers.config import config
from helpers.handler import Handler
from helpers.member_cache import MemberCache

logger = logging.getLogger(__name__)

VATSIM_BASE_URL = 'https://data.vatsim.net'
VATSIM_DATA = '/v3/vatsim-data.json'


class VATSIMDataFetchException(Exception):
    """Exception raised when fetching VATSIM data."""

    status_code: int

    def __init__(self, response: aiohttp.ClientResponse):
        self.status_code = response.status
        super().__init__(f'Failed to fetch VATSIM data: HTTP {self.status_code}')


class MemberNickUpdateException(Exception):
    """Failed to update the nickname of a member."""

    def __init__(self, member: Member, *args):
        super().__init__(*args)


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
        self._allowed_callsigns_pattern = config.COORDINATION_ALLOWED_CALLSIGNS
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
        """
        Update the cache of online controllers periodically

        Note:
            Once the online controllers map has been populated, this will also initate
            an update of all current voice channel members in the gulid.

        Todo:
            - Consider splitting voice channel members update into a separate task.

        """
        try:
            logger.debug('Updating online controllers cache...')
            self._online_controllers = await self._fetch_online_controllers()
            self._last_update = datetime.datetime.now()
            await self._update_voice_channel_members()
        except Exception:
            logger.exception('Failed to update controllers cache')

    async def _get_controller_station(self, cid: int) -> Optional[str]:
        """Get the controller's prefix if they're online, None otherwise"""
        if cid in self._online_controllers:
            return self._online_controllers[cid].replace('__', '_')
        return None

    async def _restore_nickname(self, member: discord.Member) -> None:
        """Restore the original nickname of a member"""
        modified_member = self._member_cache.get(member.id)
        if not modified_member:
            # TODO(thor): eliminate this warning and replace it with a debug as it is normal
            logger.warning('Original nickname not found', extra={member: member})
            return

        original_nick = modified_member['nick']
        # Remove the nickname first to avoid issue for those weird users who have higher permissions
        # than the bot itself. This is an additional risk, but one we're fine to make.
        _create_task(self._member_cache.remove_nickname(member.id))
        await member.edit(
            nick=original_nick,
            reason='Removing callsign prefix after leaving voice channel',
        )

    def _format_name(self, prefix: str, name: Optional[str], cid: int) -> str:
        if name is None:
            return f'{prefix}: |-{cid}-|'
        return f'{prefix}: {name} - {cid}'

    def _feature_enabled(self, cid: int, callsign: Optional[str] = None) -> bool:
        """Simple feature gate for gradual rollout"""
        # TODO(thor): remove after validation
        if cid in self._allowed_cids:
            return True

        if (
            callsign
            and self._allowed_callsigns_pattern
            and re.match(self._allowed_callsigns_pattern, callsign)
        ):
            return True

        logger.info(f"Skipping {cid=} and {callsign=} as it's not enabled")
        return False

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

            if not cid and not name:
                # We weren't able to extract either of the name and CID, so we can't proceed
                return

            callsign = await self._get_controller_station(cid)
            if not self._feature_enabled(cid, callsign):
                return

            modified_member = self._member_cache.get(member.id)
            if modified_member and not callsign:
                # Modified members without callsigns should be restored
                await self._restore_nickname(member)
                return

            if not callsign:
                # If there's no callsign, then there's nothing to do
                return

            # Add the prefix to the user and and store original nickname before modification
            if modified_member:
                # We have a modified member, so we need to update their nickname
                cid = modified_member['cid']
                name = modified_member['name']
                await self._set_member_nickname(member, callsign, name, cid)
            else:
                current_nick = member.nick or member.name
                _create_task(
                    self._member_cache.store(
                        member_id=member.id, nick=current_nick, name=name, cid=cid
                    )
                )
                await self._set_member_nickname(member, callsign, name, cid)

        except discord.Forbidden:
            logger.warning(f'Bot lacks permission to change nickname of {member}')
        except Exception:
            logger.exception(f'Error updating nickname for {member}')

    async def _set_member_nickname(
        self, member: discord.Member, callsign: str, name: str, cid: int
    ) -> None:
        """Set the nickname for a member"""
        new_name = self._format_name(callsign, name, cid)
        if name is not None:
            max_length = max(0, len(name) - (len(new_name) - 32))
            short_name = _ellipsify(name, max_length)
            new_name = self._format_name(callsign, short_name, cid)

        if len(new_name) > 32:
            raise ValueError(f'New name exceeds 32 characters: {new_name}')

        await member.edit(
            nick=new_name,
            reason='Adding callsign prefix after joining voice channel',
        )
        logger.info(f'Updating nickname for {member} to {new_name=}')

    async def _update_voice_channel_members(self):
        """Update all members in voice channels across all guilds"""
        tasks = []
        for guild in self._bot.guilds:
            for channel in guild.voice_channels:
                tasks.extend(
                    [self._update_member_nickname(member) for member in channel.members]
                )
        _create_task(*tasks)

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
        except Exception:
            logger.exception('Error in update_voice command')
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
