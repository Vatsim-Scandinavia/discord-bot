import re
import requests
import aiohttp
from typing import List, Any, Optional
from datetime import datetime, timedelta
from discord.ext.commands import Bot, Context

from helpers.booking import Booking
from helpers.db import DB
from services.events import EventService
import helpers.staffings.messages as ask


class StaffingAsync():

    def __init__(self, *, base_url: str, calendar_type: str, token: str) -> None:
        self.events = EventService(base_url=base_url, calendar_type=calendar_type, token=token)

    #
    # ----------------------------------
    # ASYNC DATA FUNCTIONS
    # ----------------------------------
    #
    async def _get_titles(self) -> List[str]:
        """
        Function to fetch and return a list of unique event titles from the database
        excluding titles already used in staffing.
        """
        # Fetch staffing titles from the database
        staffings = DB.select(table="staffing", columns=['title'], amount='all')
        formatted_staffings = {str(staffing[0]) for staffing in staffings}
        
        # Get event titles excluding existing staffings
        return await self.events.get_event_titles(exclude_titles=formatted_staffings)

    def _get_avail_titles(self) -> List[str]:
        staffings = DB.select(table="staffing", columns=['title'], amount='all')
    
        if not staffings:
            return ['None is available. Please try again later.']
        
        # Use a set to avoid duplicates
        formatted_staffings = {str(staffing[0]) for staffing in staffings}

        return list(set(formatted_staffings))
    
    async def _fetch_data(self, endpoint: str, params: Optional[dict] = None) -> Optional[List[Any]]:
        """
        Generic method to fetch data from the API.

        Args:
            endpoint (str): The API endpoint to query.
            params (dict, optional): Query parameters to include in the request.

        Returns:
            Optional[List[Any]]: The parsed JSON response data or None if the request fails.
        """
        url = f"{self.base_url}/{endpoint}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        resp = await response.json()
                        data = resp.get("data", [])
                        if data:
                            return data
                        
                        return resp
                    else:
                        print(f"Error fetching data from {url}. Status code: {response.status}")
                        return None
            except aiohttp.ClientError as e:
                print(f"HTTP error occurred while accessing {url}: {e}")
                return None
        
    async def _setup_section_pos(self, bot: Bot, ctx: Context, title):
        """
        Function gets the positions of the event from a message that'll be included in the staffing message
        """
        try:
            position = {}
            times = await StaffingAsync.get_howmanypositions(self, bot, ctx, title)

            i = 1
            for _ in range(int(times)):
                await ctx.send(f'{title} nr. {i}? **FYI this command expires in 1 minute**')
                message = await bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)
                start_time = await ask.get_start_or_end_time(bot, ctx, 'start time')
                end_time = await ask.get_start_or_end_time(bot, ctx, 'end time')
                local_booking = await ask.get_local_booking(bot, ctx)
                position[message.content + ':'] = {
                    'position': message.content + ':',
                    'start_time': start_time,
                    'end_time': end_time,
                    'local_booking': local_booking
                }
                i += 1

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No positions was provided.')
                raise ValueError

            return position

        except Exception as e:
            await ctx.send(f'Error getting {title} - {e}')
            raise e

    async def _geteventdate(self, title: str, interval = 1):
        """Get date of event, start time, end time and new event date based on interval."""
        event_data = await self.events.get_event_details(title)
        if not event_data:
            return None, None, None, None

        # Extract event start and end times
        start_time = event_data.get("start_date")
        end_time = event_data.get("end_date")

        if not start_time:
            print(f"Start time not found for event '{title}'.")
            return None, None, None, None

        start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        formatted_start_time = start_time.strftime("%H:%M")

        # Handle missing end time
        if end_time:
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        else:
            end_time = (start_time + timedelta(hours=2)).strftime("%H:%M")

        # Calculate new event date based on interval
        today = datetime.today()
        days = (start_time.weekday() - today.weekday() + interval * 7) % (interval * 7)
        newdate = today + timedelta(days=days)

        # Get current scheduled date if staffing exists
        current = None
        staffing_exists = DB.select(table="staffing", columns=['title'], amount="all")
        if title in [item[0] for item in staffing_exists]:
            current = DB.select(table="staffing", columns=['date'], where=['title'], value={'title': title})[0]

        return newdate, formatted_start_time, end_time, current

    async def _updatemessage(self, bot: Bot, id):
        try:
            event = DB.select(table='staffing', columns=['*'], where=['id'], value={'id': id})

            title = event[1]
            description = event[3]
            channel_id = event[4]
            message_id = event[5]
            interval = event[6]
            first_section = event[7]
            second_section = event[8]
            third_section = event[9]
            fourth_section = event[10]

            dates = await self._geteventdate(title, interval)
            start_time = dates[1]
            end_time = dates[2]

            format_staffing_message = ""

            if format_staffing_message != "":
                format_staffing_message += "\n"

            date = dates[3]
            if date is None:
                date = dates[0]
            formatted_date = date.strftime("%A %d/%m/%Y")

            section_positions = {}
            section_positions[first_section] = DB.select(table='positions', columns=['*'], where=['event', 'type'], value={'event': id, 'type': 1}, amount='all')
            section_positions[second_section] = DB.select(table='positions', columns=['*'], where=['event', 'type'], value={'event': id, 'type': 2}, amount='all')
            section_positions[third_section] = DB.select(table='positions', columns=['*'], where=['event', 'type'], value={'event': id, 'type': 3}, amount='all')
            section_positions[fourth_section] = DB.select(table='positions', columns=['*'], where=['event', 'type'], value={'event': id, 'type': 4}, amount='all')


            pos_info = ''
            for x in section_positions:
                if x is not None:
                    pos_data = []
                    for pos in section_positions[x]:
                        if pos[6] is not None and pos[7] is not None:
                            pos_data.append(f':'.join(str(pos[6]).split(':')[:2]) + ' - ' + ':'.join(str(pos[7]).split(':')[:2]) + f' ‖ {pos[1]} {pos[2]}')
                        else:
                            pos_data.append(f'{pos[1]} {pos[2]}')
                    pos_info += f'\n\n{x}:\n' + '\n' .join(position for position in pos_data)
                
            format_staffing_message += f'{title} staffing - {formatted_date} {start_time} - {end_time}z\n\n{description}{pos_info}'

            channel = bot.get_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            await message.edit(content=format_staffing_message)

        except Exception as e:
            print(f'Unable to update message - {e}', flush=True)
            raise e

    async def _book(self, bot, ctx, eventDetails, event, usernick, position, section):
        cid = re.findall(r"\d+", str(ctx.author.nick))[0]

        positions = DB.select(table="positions", columns=['*'], where=['event'], value={'event': event[0]}, amount='all')
        sections = DB.select(table="staffing", columns=['section_1_title', 'section_2_title', 'section_3_title', 'section_4_title'], where=['id'], value={'id': event[0]})
        
        section_1 = sections[0].lower() if sections[0] != None else None
        section_2 = sections[1].lower() if sections[1] != None else None
        section_3 = sections[2].lower() if sections[2] != None else None
        section_4 = sections[3].lower() if sections[3] != None else None

        sections = {
            section_1: '1',
            section_2: '2',
            section_3: '3',
            section_4: '4'
        }

        time = await self._geteventdate(event[1])

        tag = 3

        date = datetime.strptime(str(eventDetails[0]), '%Y-%m-%d')
        date = date.strftime("%d/%m/%Y")

        start_time = None
        end_time = None
        booking = False
        for pos in positions:
            if pos[6] == '00:00:00' or pos[6] == None:
                start_time = time[1]
            else:
                start_time = ':'.join(str(pos[6]).split(':')[:2])

            if pos[7] == '00:00:00' or pos[7] == None:
                end_time = time[2]
            else:
                end_time = ':'.join(str(pos[7]).split(':')[:2])
            
            if booking is False:
                if section is None and position.upper() + ':' == pos[1] and pos[2] == '':
                    if int(pos[5]) == 0:
                        request = await Booking.post_booking(self, int(cid), str(date), str(start_time), str(end_time), str(position), int(tag))

                        if request.status_code == requests.codes.ok:
                            feedback = request.json()['booking']
                            DB.update(self=self, table='positions', columns=['user'], values={'user': f'<@{usernick}>'}, where=['position', 'user', 'event'], value={'position': f'{position.upper()}:', 'user': '', 'event': event[0]}, limit=1)
                            
                            selected = DB.select(table="positions", columns=['*'], where=['position', 'user', 'event'], value={'position': f'{position.upper()}:', 'user': f'<@{usernick}>', 'event': event[0]}, amount='all')
                            
                            for select in selected:
                                if select[3] == '':
                                    DB.update(self=self, table='positions', columns=['booking_id'], values={'booking_id': feedback['id']}, where=['id'], value={'id': select[0]})

                            await self._updatemessage(bot, event[0])
                            await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{event[1]}`", delete_after=5)
                            booking = True
                        else:
                            await ctx.send(f"<@{usernick}> Booking failed, Control Center responded with error `{request.json()['message']}` code `{request.status_code}`, please try again later", delete_after=5)

                    else:
                        DB.update(self=self, table='positions', columns=['user'], values={'user': f'<@{usernick}>'}, where=['position', 'user', 'event'], value={'position': f'{position.upper()}:', 'user': '', 'event': event[0]}, limit=1)
                        await self._updatemessage(bot, event[0])
                        await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{event[1]}`", delete_after=5)
                        booking = True
                elif section is not None:
                    if sections[section] == pos[4] and position.upper() + ':' == pos[1] and pos[2] == '':
                        if int(pos[5]) == 0:
                            request = await Booking.post_booking(self, int(cid), str(date), str(start_time), str(end_time), str(position), int(tag))

                            if request.status_code == requests.codes.ok:
                                feedback = request.json()['booking']
                                DB.update(self=self, table='positions', columns=['user'], values={'user': f'<@{usernick}>'}, where=['position', 'type', 'user', 'event'], value={'position': f'{position.upper()}:', 'type': sections[section], 'user': '', 'event': event[0]}, limit=1)
                                selected = DB.select(table="positions", columns=['*'], where=['position', 'type', 'user', 'event'], value={'position': f'{position.upper()}:', 'type': sections[section], 'user': f'<@{usernick}>', 'event': event[0]}, amount='all')

                                for select in selected:
                                    if select[3] == '':
                                        DB.update(self=self, table='positions', columns=['booking_id'], values={'booking_id': feedback['id']}, where=['id'], value={'id': select[0]})


                                await self._updatemessage(bot, event[0])
                                await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{event[1]}`", delete_after=5)
                                booking = True
                            else:
                                await ctx.send(f"<@{usernick}> Booking failed, Control Center responded with error `{request.json()['message']}` code `{request.status_code}`, please try again later", delete_after=5)
                        else:
                            DB.update(self=self, table='positions', columns=['user'], values={'user': f'<@{usernick}>'}, where=['position', 'type', 'user', 'event'], value={'position': f'{position.upper()}:', 'type': sections[section], 'user': '', 'event': event[0]}, limit=1)
                            await StaffingAsync._updatemessage(self, bot, event[0])
                            await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{event[1]}`", delete_after=5)
                            booking = True

        if booking == False:
            await ctx.send(f'<@{usernick}> Booking failed, check if you inserted correct postion, section or if the positions is already booked.', delete_after=5)