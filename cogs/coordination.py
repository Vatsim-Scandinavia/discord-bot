import asyncio
import datetime
import re
from asyncio import Task
from collections.abc import Coroutine
from typing import Any

import aiohttp
import discord
import structlog
from discord import app_commands
from discord.ext import commands, tasks

from helpers.config import config
from helpers.handler import Handler
from helpers.member_cache import MemberCache

logger = structlog.stdlib.get_logger()

VATSIM_BASE_URL = 'https://data.vatsim.net'
VATSIM_DATA = '/v3/vatsim-data.json'

_POSITION_LOGON_NORMALIZER = re.compile('_+')

OnlineControllers = dict[int, str]
"""A dictionary mapping VATSIM controller CIDs to their callsigns"""


class VATSIMDataFetchException(Exception):
    """Exception raised when fetching VATSIM data."""

    status_code: int

    def __init__(self, response: aiohttp.ClientResponse):
        self.status_code = response.status
        super().__init__(f'Failed to fetch VATSIM data: HTTP {self.status_code}')


class MemberNickUpdateException(Exception):
    """Failed to update the nickname of a member."""


class NewNickTooLongException(Exception):
    """New nickname exceeds the maximum length."""

    def __init__(self, nick: str):
        super().__init__(f'New nickname exceeds 32 characters: {nick}')


class AttemptingDuplicatePrefixException(Exception):
    """Attempting to set a name with a prefix"""

    def __init__(self, name: str):
        super().__init__(
            f'Attempting to dual-prefix a nick that is already prefixed: {name}'
        )


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

    coordination = app_commands.Group(
        name='coordination',
        description='Manually handle coordination fixes',
        guild_only=True,
    )

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._handler = Handler()
        self._callsign_separator = config.COORDINATION_CALLSIGN_SEPARATOR
        self._last_update: datetime.datetime | None = None
        self._session = aiohttp.ClientSession(base_url=VATSIM_BASE_URL)
        self._online_controllers: OnlineControllers = {}
        self._member_cache = MemberCache(folder=config.CACHE_DIR)
        self._update_controllers_cache.start()
        # TODO(thor): remove this allow list after validation #122
        self._allowed_cids = config.COORDINATION_ALLOWED_CIDS
        self._allowed_callsigns_pattern = config.COORDINATION_ALLOWED_CALLSIGNS
        logger.info('Initialized and started updating controllers cache')

    async def cog_unload(self):
        self._update_controllers_cache.cancel()
        await self._session.close()
        await self._clean_up()
        logger.info('Stopped updating cache and attempted restoring existing members')

    async def has_modified_nick(self, member: discord.Member) -> bool:
        """Check if a member has a modified nickname"""
        return (
            member.nick is not None
            and self._callsign_separator in member.nick
            and self._member_cache.get(member.id) is not None
        )

    async def _clean_up(self):
        ids = self._member_cache.get_member_ids()
        members = self._bot.get_all_members()
        tasks = [
            self._process_member(member=member, force_remove=True)
            for member in members
            if member.id in ids
        ]
        _create_task(*tasks)

    async def _fetch_online_controllers(self) -> OnlineControllers:
        """Fetch online controllers from VATSIM Datafeed API"""
        try:
            async with self._session.get(VATSIM_DATA) as response:
                if response.status != 200:
                    raise VATSIMDataFetchException(response)
                data = await response.json()
            controllers: dict[int, str] = {}
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
            logger.exception(
                'Failed to update controllers cache', last_update=self._last_update
            )

    async def _get_controller_station(self, cid: int) -> str | None:
        """Get the controller's prefix if they're online, None otherwise"""
        if cid in self._online_controllers:
            return self._online_controllers[cid].replace('__', '_')
        return None

    async def _restore_nickname(self, member: discord.Member, reason: str) -> None:
        """Restore the original nickname of a member"""
        if not member.nick:
            return

        log = logger.bind(id=member.id, name=member.name, nick=member.nick)
        modified_member = self._member_cache.get(member.id)
        if not modified_member:
            if self._callsign_separator and self._callsign_separator in member.nick:
                # This is the case where a user for some reason has a prefix, but we've
                # failed to store their original nickname. This should error.
                log.error('Can not restore nickname without original nickname')
                return
            # No prefix characters identified: that's fine.
            log.debug('No modification record found, skipping nick restoration')
            return

        original_nick = modified_member['nick']
        # Remove the nickname first to avoid issue for those weird users who have higher permissions
        # than the bot itself. This is an additional risk, but one we're fine to make.
        log.info(
            'Removing and restoring nick', stored_nick=original_nick, reason=reason
        )
        _create_task(self._member_cache.remove_nickname(member.id))
        await member.edit(nick=original_nick, reason=reason)

    def _format_name(self, prefix: str, name: str | None, cid: int) -> str:
        """Format the name for the member's nickname"""
        prefix = prefix.removesuffix('_CTR')
        prefix = _POSITION_LOGON_NORMALIZER.sub(' ', prefix)
        prefix = prefix.replace(' I TWR', ' AFIS')

        # TODO(thor): This is a bit of a hack to support non-name nicknames
        if name is None:
            return f'{prefix} {self._callsign_separator} |-{cid}-|'

        return f'{prefix} {self._callsign_separator} {name} - {cid}'

    def _feature_enabled(self, cid: int, callsign: str | None = None) -> bool:
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

        logger.info('Skipping member outside of rollout', cid=cid, callsign=callsign)
        return False

    async def _process_member(
        self, member: discord.Member, force_remove: bool = False
    ) -> None:
        """Process and update member's nickname depending on control activity"""
        log = logger.bind(member=member.name, nick=member.nick)
        try:
            if not member.voice:
                await self._restore_nickname(member, reason='Left voice channel')
                return

            if force_remove:
                await self._restore_nickname(member, reason='Forcibly removed')
                return

            cid = self._handler.get_cid(member)
            name = self._handler.get_name(member)

            if not cid and not name:
                # We weren't able to extract either of the name and CID, so we can't proceed
                log.warning("Couldn't extract CID or name from member's nickname")
                return

            callsign = await self._get_controller_station(cid)
            modified_member = self._member_cache.get(member.id)
            if modified_member and not callsign:
                # Modified members without callsigns should be restored
                await self._restore_nickname(
                    member, reason='No longer actively controlling'
                )
                return

            if not callsign or not member.nick:
                # If there's no callsign, then there's nothing to do
                return

            # TODO(thor): remove after validation #122
            if not self._feature_enabled(cid, callsign):
                return

            # Add the prefix to the user and and store original nickname before modification
            if modified_member:
                # We have a modified member, so we need to update their nickname
                cid = modified_member['cid']
                name = modified_member['name']
            else:
                # Before proceeding, we do a sanity check on the name
                # If it already has the separator in it, then something's wrong, and we
                # do not want to save said incorrect state nick in the member cache.
                current_nick = member.nick
                if self._callsign_separator in current_nick:
                    log.error(
                        'Unmodified user already has separator in nick',
                        callsign=callsign,
                    )
                    raise AttemptingDuplicatePrefixException(current_nick)

                # Now that we know that there isn't a callsign separator in the nick,
                # we should be safe to store it assuming we haven't run afoul of race conditions.
                await self._member_cache.store(
                    member_id=member.id, nick=current_nick, name=name, cid=cid
                )

            await self._set_member_nickname(member, callsign, name, cid)

        except discord.Forbidden:
            log.warning('Bot lacks permission to change nickname')
        except Exception:
            log.exception('Error updating nickname')

    async def _set_member_nickname(
        self, member: discord.Member, callsign: str, name: str | None, cid: int
    ) -> None:
        """Set the nickname for a member"""
        if name and self._callsign_separator in name:
            raise AttemptingDuplicatePrefixException(name=name)

        new_name = self._format_name(callsign, name, cid)
        if name is not None:
            max_length = max(0, len(name) - (len(new_name) - 32))
            short_name = _ellipsify(name, max_length)
            new_name = self._format_name(callsign, short_name, cid)

        # Early return if the correct callsign is already part of the nick
        if member.nick == new_name:
            logger.info(
                'Skipping update because nick is already set',
                member=member.name,
                nick=new_name,
            )
            return

        if len(new_name) > 32:
            raise NewNickTooLongException(new_name)

        logger.info(
            'Updating nickname',
            name=member.name,
            old_nick=member.nick,
            new_nick=new_name,
        )
        await member.edit(
            nick=new_name,
            reason='Adding callsign prefix after joining voice channel',
        )

    async def _update_voice_channel_members(self):
        """Update all members in voice channels across all guilds"""
        tasks: list[Coroutine[Any, Any, None]] = []
        for guild in self._bot.guilds:
            for channel in guild.voice_channels:
                tasks.extend(
                    [self._process_member(member) for member in channel.members]
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
        if before.channel and after.channel:
            # The user is still connected to a voice channel
            return

        if after.channel:
            # The user joined a new voice channel, doesn't matter which
            await self._process_member(member)
            return

        # User left voice voice channels altogether
        await self._process_member(member, force_remove=True)

    @coordination.command(
        name='update-voice', description='Update voice channel member nicknames'
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def update_voice(self, interaction: discord.Interaction):
        """Manually update all voice channel member nicknames"""
        try:
            await interaction.response.defer(ephemeral=True)
            await self._update_controllers_cache()
            await interaction.followup.send(
                'Voice channel nicknames updated.', ephemeral=True
            )
        except Exception:
            logger.exception('Error in update_voice command')
            await interaction.followup.send(
                'An error occurred while updating nicknames.', ephemeral=True
            )


async def setup(bot: commands.Bot):
    cog = CoordinationCog(bot)
    await bot.add_cog(cog)


_background_tasks: set[Task[None]] = set()


def _create_task(*coroutines: Coroutine[Any, Any, None]):
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
