# Linting ignored due to staffing module getting a major refactor.
import asyncio
from collections import defaultdict
from datetime import datetime

import discord

from helpers.api import APIHelper
from helpers.handler import Handler


class StaffingAsync:
    def __init__(self) -> None:
        self.api_helper = APIHelper()

    #
    # ----------------------------------
    # ASYNC DATA FUNCTIONS
    # ----------------------------------
    #

    async def _get_avail_titles(self) -> list[str]:
        staffings = await self.api_helper._fetch_data('staffings')

        if not staffings:
            return list[set('None is available. Please try again later.', 'none')]

        formatted_staffings = []

        for staffing in staffings:
            event = staffing.get('event', {})
            title = str(event.get('title', ''))
            staffing_id = str(staffing.get('id', ''))

            if title and staffing_id:
                formatted_staffings.append((title, staffing_id))

        return list(set(formatted_staffings))

    async def _generate_staffing_message(self, id):
        try:
            staffing = await self.api_helper._fetch_data(f'staffings/{id}')

            if not staffing:
                print('Error: Staffing not found.')
                raise ValueError

            event = staffing.get('event', {})

            date = event.get('start_date')
            end_date = event.get('end_date')

            if not date or not end_date:
                print('Error: Start or end date not found for event.')
                raise ValueError

            formatted_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime(  # noqa: DTZ007
                '%A %d/%m/%Y'
            )
            start_time = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')  # noqa: DTZ007
            end_time = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S').strftime(  # noqa: DTZ007
                '%H:%M'
            )

            positions = staffing.get('positions', [])

            if not positions:
                print('Error: No positions found for the event.')
                raise ValueError

            section_positions = defaultdict(list)
            section_titles = {
                1: staffing.get('section_1_title'),
                2: staffing.get('section_2_title'),
                3: staffing.get('section_3_title'),
                4: staffing.get('section_4_title'),
            }

            for position in positions:
                section = int(position.get('section', 0))
                if section_titles.get(section):
                    section_positions[section_titles[section]].append(position)

            pos_info = '\n\n'.join(
                f'{title}:\n'
                + '\n'.join(
                    (
                        f'{self.format_time(pos.get("start_time") or event.get("start_date"))} - {self.format_time(pos.get("end_time") or event.get("end_date"))} ‖ {pos.get("callsign", "")}: <@{pos.get("discord_user")}>'
                        if pos.get('discord_user')
                        and (pos.get('start_time') or pos.get('end_time'))
                        else f'{self.format_time(pos.get("start_time") or event.get("start_date"))} - {self.format_time(pos.get("end_time") or event.get("end_date"))} ‖ {pos.get("callsign", "")}:'
                        if pos.get('start_time') or pos.get('end_time')
                        else f'{pos.get("callsign", "")}: <@{pos.get("discord_user")}>'
                        if pos.get('discord_user')
                        else f'{pos.get("callsign", "")}:'
                    )
                    for pos in positions
                )
                for title, positions in section_positions.items()
                if title
            )

            description = staffing.get('description', '')

            format_staffing_message = f'{event.get("title", "")} staffing - {formatted_date} {start_time} - {end_time}z\n\n{description}\n\n{pos_info}'

            return staffing, format_staffing_message

        except Exception as e:
            print(f'Unable to update message - {e}', flush=True)
            raise

    def format_time(self, value):
        if isinstance(value, str):
            try:
                # Handle full datetime string like '2025-03-17 21:00:00'
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')  # noqa: DTZ007
                return dt.strftime('%H:%M')
            except ValueError:
                # If it's already in correct format like '21:00'
                return value[:5]
        return ''

    def _generate_thread_name(self, event):
        """
        Generate thread name in format: "{event_title} - {date}"
        where date is formatted as DD/MM/YYYY.
        """
        event_title = event.get('title', '')
        date = event.get('start_date')

        if not date:
            # Fallback to just event title if no date
            return event_title or 'Staffing'

        try:
            formatted_date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').strftime(  # noqa: DTZ007
                '%d/%m/%Y'
            )
            return f'{event_title} - {formatted_date}'
        except ValueError:
            # If date parsing fails, return just title
            return event_title or 'Staffing'

    async def _resolve_staffing_channel_and_message(self, bot, staffing):
        """
        Resolve the channel/thread and message for a staffing.

        Returns:
            tuple: (channel_or_thread, message)

        Raises:
            ValueError: If required IDs are missing or channel/thread/message not found.

        """
        use_threads = staffing.get('use_threads', False) or staffing.get('is_thread', False)
        message_id = staffing.get('message_id', 0)

        if not message_id:
            raise ValueError('Message ID not found in staffing data.')

        if use_threads:
            thread_id = staffing.get('thread_id')
            if not thread_id:
                raise ValueError('Thread ID not found for thread-based staffing.')

            thread = bot.get_channel(int(thread_id))
            if not thread:
                msg = 'Thread with ID {} not found.'.format(thread_id)
                raise ValueError(msg)

            try:
                message = await thread.fetch_message(int(message_id))
            except discord.NotFound as err:
                msg = 'Message with ID {} not found in thread {}.'.format(message_id, thread_id)
                raise ValueError(msg) from err

            return thread, message

        channel_id = staffing.get('channel_id', 0)
        if not channel_id:
            raise ValueError('Channel ID not found for channel-based staffing.')

        channel = bot.get_channel(int(channel_id))
        if not channel:
            msg = 'Channel with ID {} not found.'.format(channel_id)
            raise ValueError(msg)

        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound as err:
            msg = 'Message with ID {} not found in channel {}.'.format(message_id, channel_id)
            raise ValueError(msg) from err

        return channel, message

    async def _book(self, ctx, staffing, position, section):
        try:
            cid = Handler.get_cid(self, ctx.author)

            sections_map = {
                (staffing.get('section_1_title') or '').lower(): '1',
                (staffing.get('section_2_title') or '').lower(): '2',
                (staffing.get('section_3_title') or '').lower(): '3',
                (staffing.get('section_4_title') or '').lower(): '4',
            }

            # Get event details
            event = staffing.get('event', {})

            if not event:
                await ctx.send(
                    f'<@{ctx.author.id}> Booking failed: Event not found for this staffing. Please contact Tech.',
                    ephemeral=True,
                )
                return

            # Validate section
            section_id = None
            if section:
                if section not in sections_map:
                    await ctx.send(
                        f'<@{ctx.author.id}> Booking failed: Invalid section `{section}`. Must be one of {list(sections_map.keys())}',
                        ephemeral=True,
                    )
                    return

                section_id = sections_map[section]

                if not (1 <= int(section_id) <= 4):  # Double-check it's between 1-4
                    await ctx.send(
                        f'<@{ctx.author.id}> Booking failed: Section `{section_id}` must be between 1 and 4.',
                        ephemeral=True,
                    )
                    return

            params = {
                'cid': int(cid),
                'position': position,
                'message_id': staffing.get('message_id', 0),
                'discord_user_id': ctx.author.id,
                **({'section': section_id} if section_id is not None else {}),
            }

            request = await self.api_helper.post_data('staffings/book', params)

            if request:
                await ctx.send(
                    f'<@{ctx.author.id}> Confirmed booking for position `{position.upper()}` for event `{event.get("title", "")}`',
                    delete_after=5,
                    ephemeral=True,
                )
                return

        except Exception as e:
            await ctx.send(
                f'Error booking position `{position}` - {e}',
                delete_after=5,
                ephemeral=True,
            )
            raise

    async def update_staffing_message(self, bot, id, reset=None):
        staffing, staffing_msg = await self._generate_staffing_message(id)

        if not staffing or not staffing_msg:
            print('Failed to generate staffing message.')
            raise ValueError

        try:
            channel_or_thread, message = await self._resolve_staffing_channel_and_message(
                bot, staffing
            )
        except (ValueError, discord.NotFound) as e:
            print(f'Error resolving staffing channel/message: {e}')
            raise

        await message.edit(content=staffing_msg)

        if reset:
            event = staffing.get('event', {})
            title = event.get('title', '')
            print(f'Started autoreset of {title} at {datetime.now().isoformat()!s}')

            await channel_or_thread.send('The chat is being automatic reset!')
            await asyncio.sleep(5)
            await channel_or_thread.purge(limit=None, check=lambda msg: not msg.pinned)

            print(
                f'Finished autoreset of {title} at {datetime.now().isoformat()!s}',
                flush=True,
            )
