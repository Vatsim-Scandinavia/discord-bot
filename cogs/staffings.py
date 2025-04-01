import asyncio
from datetime import datetime
from typing import Optional

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from helpers.api import APIHelper
from helpers.config import config
from helpers.handler import Handler
from helpers.staffing_async import StaffingAsync


class StaffingCog(commands.Cog):
    #
    # ----------------------------------
    # COG FUNCTIONS
    # ----------------------------------
    #
    def __init__(self, bot) -> None:
        self.bot = bot
        self.staffing_async = StaffingAsync()
        self.api_helper = APIHelper()

    #
    # ----------------------------------
    # SLASH COMMAND FUNCTIONS
    # ----------------------------------
    #

    # Autocomplete function to fetch and filter titles in real-time
    async def avail_title_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice]:
        # Fetch the latest available titles from the database
        staffings = await self.staffing_async._get_avail_titles()

        # Return titles that match the user's input
        return [
            app_commands.Choice(name=title, value=staffing_id)
            for title, staffing_id in staffings
            if current.lower() in title.lower()
        ]

    @app_commands.command(
        name='refreshevent', description='Bot refreshes selected event'
    )
    @app_commands.describe(staffing='Which staffing would you like to refresh?')
    @app_commands.autocomplete(staffing=avail_title_autocomplete)
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def refreshevent(self, interaction: discord.Interaction, staffing: int):
        ctx = await Handler.get_context(self, self.bot, interaction)

        staffing, staffing_msg = await self.staffing_async._generate_staffing_message(
            staffing
        )

        event = staffing.get('event', '')
        title = event.get('title', '')

        channel = self.bot.get_channel(int(staffing.get('channel_id', 0)))
        message = await channel.fetch_message(int(staffing.get('message_id', 0)))

        await message.edit(content=staffing_msg)
        await ctx.send(
            f'{ctx.author.mention} Event `{title}` has been refreshed',
            delete_after=5,
            ephemeral=True,
        )

    @app_commands.command(
        name='manreset', description='Bot manually resets selected event'
    )
    @app_commands.describe(staffing='Which staffing would you like to manually reset?')
    @app_commands.autocomplete(staffing=avail_title_autocomplete)
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def manreset(self, interaction: discord.Integration, staffing: int):
        ctx = await Handler.get_context(self, self.bot, interaction)

        try:
            staffing = await self.api_helper._fetch_data(f'staffings/{staffing}')

            event = staffing.get('event', {})
            title = event.get('title', '')

            await ctx.send(
                f'{ctx.author.mention} Started manual reset of `{title}` at `{datetime.now().isoformat()!s}`',
                delete_after=5,
                ephemeral=True,
            )

            staffing_id = staffing.get('id', 0)

            # Send API POST request
            request = await self.api_helper.post_data(
                f'staffings/{staffing_id}/reset', {}
            )

            if not request:
                await ctx.send(
                    f'{ctx.author.mention} The bot failed to manual reset `{title}` at `{datetime.now().isoformat()!s}`',
                    ephemeral=True,
                )
                return

            channel = self.bot.get_channel(int(staffing.get('channel_id', 0)))

            await channel.send('The chat is being automatic reset!')
            await asyncio.sleep(5)
            await channel.purge(limit=None, check=lambda msg: not msg.pinned)

            await ctx.send(
                f'{ctx.author.mention} Finished manual reset of `{title}` at `{datetime.now().isoformat()!s}`',
                delete_after=5,
                ephemeral=True,
            )
        except Exception as e:
            await ctx.send(
                f'{ctx.author.mention} The bot failed to manual reset `{title}` with error `{e}` at `{datetime.now().isoformat()!s}`',
                ephemeral=True,
            )

    @app_commands.command(
        name='book', description='Bot books selected position for selected staffing'
    )
    @app_commands.describe(position='Which position would you like to book?')
    @app_commands.check(Handler.is_obs)
    async def book(
        self,
        interaction: discord.Integration,
        position: str,
        section: Optional[str] = None,
    ):
        ctx = await Handler.get_context(self, self.bot, interaction)
        user_id = ctx.author.id

        try:
            allowed_roles = {config.VATSIM_MEMBER_ROLE, config.VATSCA_MEMBER_ROLE}
            if not any(role.id in allowed_roles for role in ctx.author.roles):
                await ctx.send(
                    f'<@{user_id}> You do not have the required role to book positions.',
                    delete_after=5,
                    ephemeral=True,
                )
                return

            staffings = await self.api_helper._fetch_data('staffings')
            staffing = next(
                (s for s in staffings if s.get('channel_id') == ctx.channel.id), None
            )

            if not staffing:
                await ctx.send(
                    f'<@{user_id}> Please use the correct channel.',
                    delete_after=5,
                    ephemeral=True,
                )
                return

            section = (section or '').lower()

            await self.staffing_async._book(ctx, staffing, position, section)
        except Exception as e:
            print(f'Error booking position {position} - {e}')

            await ctx.send(f'Error booking position {position} - {e}')
            raise

    @app_commands.command(
        name='unbook', description='Bot unbooks selected position for selected staffing'
    )
    async def unbook(
        self,
        interaction: discord.Integration,
        position: Optional[str] = None,
        section: Optional[str] = None,
    ):
        ctx = await Handler.get_context(self, self.bot, interaction)
        try:
            staffings = await self.api_helper._fetch_data('staffings')
            staffing = next(
                (s for s in staffings if s.get('channel_id') == ctx.channel.id), None
            )

            if not staffing:
                await ctx.send(
                    f'<@{ctx.author.id}> Please use the correct channel.',
                    ephemeral=True,
                )
                return

            event = staffing.get('event', {})

            if not event:
                print(
                    f'Unbooking failed for user {ctx.author.id}: Event not found for this staffing.'
                )

                await ctx.send(
                    f'<@{ctx.author.id}> Unbooking failed: Event not found for this staffing. Please contact Tech.',
                    ephemeral=True,
                )
                return

            position = position.upper() if position else None
            section = (section or '').lower()

            sections_map = {
                (staffing.get('section_1_title') or '').lower(): '1',
                (staffing.get('section_2_title') or '').lower(): '2',
                (staffing.get('section_3_title') or '').lower(): '3',
                (staffing.get('section_4_title') or '').lower(): '4',
            }

            section_id = None
            if section:
                if section not in sections_map:
                    await ctx.send(
                        f'<@{ctx.author.id}> Unbooking failed: Invalid section `{section}`. Must be one of {list(sections_map.keys())}',
                        ephemeral=True,
                    )
                    return

                section_id = sections_map[section]

                if not (1 <= int(section_id) <= 4):  # Double-check it's between 1-4
                    await ctx.send(
                        f'<@{ctx.author.id}> Unbooking failed: Section `{section_id}` must be between 1 and 4.',
                        ephemeral=True,
                    )
                    return

            data = {
                'discord_user_id': ctx.author.id,
                'message_id': staffing.get('message_id', 0),
                **({'position': position} if position is not None else {}),
                **({'section': section_id} if section_id is not None else {}),
            }

            request = await self.api_helper.post_data('staffings/unbook', data)

            if request:
                await ctx.send(
                    f'<@{ctx.author.id}> Confirmed unbooking for event `{event.get("title", "")}`',
                    delete_after=5,
                    ephemeral=True,
                )
                return

        except Exception as e:
            print(
                f'Error unbooking position user: {ctx.author.id} for event {event.get("title", "")} - {e}'
            )

            await ctx.send(
                f'Error unbooking position for event {event.get("title", "")} - {e}'
            )
            raise


async def setup(bot):
    await bot.add_cog(StaffingCog(bot))
