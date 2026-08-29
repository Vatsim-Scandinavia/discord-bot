"""Keeps the (sub-)division role in sync with VATSIM division membership."""

import asyncio
from typing import TYPE_CHECKING, Any

import discord
import structlog
from discord.ext import commands

from core.roles import cleanup_membership_roles
from helpers.config import config
from helpers.handler import Handler

logger = structlog.stdlib.get_logger()

# We don't instantiate these, but we need to import them for type checking
if TYPE_CHECKING:
    from collections.abc import Coroutine

    from cogs.station_prefix import StationPrefixCog


class VatsimRolesCog(commands.Cog):
    """
    Grants or revokes the (sub-)division role from VATSIM division data.

    The VATSIM member role itself is assigned by the VATSIM Community bot; this
    cog reads it as a gate and manages only the (sub-)division role.
    """

    def __init__(self, bot):
        self.bot = bot
        self.handler = Handler()

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Listen to member updates and assigns role according to the nick.

        We listen to member update events to catch changes made by the VATSIM Community bot.
        One alternative approach include listening to the audit log.

        Todo:
            This entire function should possibly be merged with the cogs.tasks.check_members routine.

        """
        if before.nick == after.nick:
            return

        station_prefix: StationPrefixCog | None = self.bot.get_cog('StationPrefixCog')  # pyright: ignore[reportAssignmentType]
        if not station_prefix:
            logger.warning(
                'Could not get the station_prefix cog; cannot check for modified nicknames.',
                user=after.name,
                nick=after.nick,
            )

        # NOTE: While this should prevent the bot from assigning roles while a member has
        # a modified (i.e. position-prefixed station) nickname, it doesn't prevent any
        # race condition from occuring *during* the user's state change (i.e. when moving
        # between or leaving voice channels).
        if station_prefix and await station_prefix.has_modified_nick(after):
            logger.info(
                'User has modified nick: skipping role assignment.',
                user=after.name,
                nick=after.nick,
            )
            return

        # Define role objects
        vatsca_member = discord.utils.get(
            after.guild.roles, id=config.VATSCA_MEMBER_ROLE
        )
        vatsim_member = discord.utils.get(
            after.guild.roles, id=config.VATSIM_MEMBER_ROLE
        )

        if not vatsca_member or not vatsim_member:
            # TODO(thor): Replace with a custom exception (which probably belongs in the core module)
            logger.error(
                'The (sub-)division or VATSIM role was not found in the guild.',
                division=config.VATSCA_MEMBER_ROLE,
                vatsim=config.VATSIM_MEMBER_ROLE,
            )
            return

        try:
            # Extract CID from nickname, clearing managed roles if the member is no longer eligible.
            cid = self.handler.get_cid(after)
            if cid is None:
                await cleanup_membership_roles(
                    after,
                    config.ROLE_REASONS['no_vatsim_role'],
                    include_vatsca=True,
                )
                return

            api_data = await self.handler.get_division_members()

            should_have_vatsca = any(
                int(entry['id']) == cid
                and str(entry['subdivision']) == str(config.VATSIM_SUBDIVISION)
                for entry in api_data
            )
            logger.info('Fetched division members from API', len=len(api_data))

            # Manage role assignments
            tasks: list[Coroutine[Any, Any, None]] = []

            if vatsim_member in after.roles:
                # add VATSCA if required otherwise remove it
                if should_have_vatsca and vatsca_member not in after.roles:
                    tasks.append(
                        after.add_roles(
                            vatsca_member, reason='Missing role in on_member_update'
                        )
                    )
                elif not should_have_vatsca and vatsca_member in after.roles:
                    tasks.append(
                        after.remove_roles(
                            vatsca_member, reason='Redundant role in on_member_update'
                        )
                    )

            elif vatsca_member in after.roles:
                # Remove VATSCA if the user doesn't have VATSIM role
                tasks.append(
                    after.remove_roles(
                        vatsca_member,
                        reason='Redunant role because VATSIM role is missing in on_member_update',
                    )
                )

            if tasks:
                await asyncio.gather(*tasks)

        except ValueError as e:
            logger.warning(
                'Failed to process member update due to invalid or missing CID; cleaning managed roles.',
                name=after.name,
                nick=after.nick,
                error=e,
            )
            await cleanup_membership_roles(
                after, config.ROLE_REASONS['no_cid'], include_vatsca=True
            )

        # TODO(thor): Replace with either custom exceptions or find out how to move them out to the core handler
        except discord.Forbidden as e:
            logger.exception('Bot lacks permission for action', error=e)

        except discord.HTTPException as e:
            logger.exception('HTTP error', error=e)

        except Exception as e:
            logger.exception('Unexpected error', error=e)


async def setup(bot: commands.Bot):
    await bot.add_cog(VatsimRolesCog(bot))
