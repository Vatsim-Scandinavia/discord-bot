import re
import requests
import aiohttp

from typing import List, Any, Optional
from datetime import datetime, timedelta

from helpers.config import config
from helpers.booking import Booking
from helpers.db import DB


class StaffingAsync():

    def __init__(self) -> None:
        self.base_url = config.EVENT_CALENDAR_URL
        self.calendar_type = config.EVENT_CALENDAR_TYPE
        self.headers = {
            "Authorization": f"Bearer {config.CC_API_TOKEN}",
            "Accept": "application/json"
        }

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
        # Fetch event names asynchronously
        events = await self._fetch_data(f"calendars/{self.calendar_type}/events")

        # Fetch staffing titles from the database
        staffings = DB.select(table="staffing", columns=['title'], amount='all')

        formatted_staffings = {str(staffing[0]) for staffing in staffings}
        formatted_events = []

        # If no events are found, append a message indicating no availability
        if not events:
            formatted_events.append('None is available. Please try again later.')
        else:
            for event in events:
                formatted_event = str(event.get('title', ''))
                # Add the event only if it is not already present in staffing
                if formatted_event and formatted_event not in formatted_staffings:
                    formatted_events.append(formatted_event)
    
        # Return a list of unique event titles
        return list(set(formatted_events))

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
        
    async def _get_description(self, ctx):
        """
        Function gets the description of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Staffing message? **FYI this command expires in 5 minutes**')
            message = await self.bot.wait_for('message', timeout=300, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as e:
            await ctx.send(f'Error getting the Staffing message - {e}')
            raise e

    async def _get_interval(self, ctx):
        """
        Function gets the week interval of the event
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Week interval? **FYI this command expires in 5 minutes**')
            message = await self.bot.wait_for('message', timeout=300, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            if int(message.content) not in range(1, 5):
                await ctx.send('The interval must be between 1 to 4')
                raise ValueError

            return message.content
        except Exception as e:
            await ctx.send(f'Error getting the Staffing message - {e}')
            raise e

    async def _get_retriction(self, ctx):
        """
        Function gets the booking restriction of the event
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Should the event have booking restriction? Allowed ansers: `Yes` or `No` **FYI this command expires in 5 minutes**')
            message = await self.bot.wait_for('message', timeout=300, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            if 'yes' in message.content.lower() or 'no' in message.content.lower():
                return message.content.lower()
            else:
                await ctx.send('Only the options `Yes` or `No` is available')
                raise ValueError

            
        except Exception as e:
            await ctx.send(f'Error getting the Staffing message - {e}')
            raise e

    async def _setup_section(self, ctx, num: int):
        """
        Function gets the title for positions of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            await ctx.send(f'Section title nr. {num}? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content

        except Exception as e:
            await ctx.send(f'Error getting the third section title - {e}')
            raise e

    async def _setup_section_pos(self, ctx, title):
        """
        Function gets the positions of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            position = {}
            times = await StaffingAsync.get_howmanypositions(self, ctx, title)

            i = 1
            for _ in range(int(times)):
                await ctx.send(f'{title} nr. {i}? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)
                start_time = await StaffingAsync._get_start_or_end_time(self, ctx, 'start time')
                end_time = await StaffingAsync._get_start_or_end_time(self, ctx, 'end time')
                local_booking = await StaffingAsync._get_local_booking(self, ctx)
                position[message.content + ':'] = {
                    'position': message.content  + ':',
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

    async def get_howmanypositions(self, ctx, type):
        """
        Function gets the how many positions of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            await ctx.send(f'How many {type} positions? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as e:
            await ctx.send(f'Error getting amount of positions - {e}')
            raise e

    async def _section_type(self, ctx):
        """
        Function gets what type of section to update
        :param ctx:
        :return:
        """
        try:
            await ctx.send(f'Which section would you like to update?**FYI this command expires in 1 minute** \nAvailable sections is: `1, 2 or 3`')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            if int(message.content) not in range(1, 4):
                await ctx.send('The section must be between 1 to 3')
                raise ValueError

            return message.content

        except Exception as e:
            await ctx.send(f'Error getting the section title - {e}')
            raise e
        
    async def _get_start_or_end_time(self, ctx, time):
        """
        Function to get the start time
        :param ctx:
        :return:
        """
        try:
            await ctx.send(f'Does this position have a specified {time}? If yes, then insert below (format: `HH:MM`), otherwise type `No`! **FYI this command expires in 1 minute**')

            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError       

            if 'no' in message.content.lower():
                return None

            return message.content
        
        except Exception as e:
            await ctx.send(f'Error getting the {time} - {e}')
            raise e
        
    async def _get_local_booking(self, ctx):
        try:
            await ctx.send(f'Is this positions a local position? Allowed ansers: `Yes` or `No` **FYI this command expires in 1 minutes**')

            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if 'yes' in message.content.lower() or 'no' in message.content.lower():
                return True if message.content.lower() == 'yes' else False
            else:
                await ctx.send('Only the options `Yes` or `No` is available')
                raise ValueError

                
        except Exception as e:
            await ctx.send(f'Error getting the local booking option - {e}')
            raise e
        
    async def _getconfirmation(self, ctx, title):
        try:
            await ctx.send(f'To confirm you want to delete staffing {title} type `{title}` in the chat. If you want to cancel the deletion type `CANCEL` in the chat. **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Deletion cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as e:
            await ctx.send(f'Error getting message - {e}')

    async def _geteventdate(self, title, interval = 1):
        """
        Get date of event, start time, end time and new event date based on interval. 
        Interval:
        1 week = 7
        2 weeks 14 and etc.
        """
        # Fetch event data using fetch_data
        events = await self._fetch_data(f"/calendars/{self.calendar_type}/events")
        staffing_exists = DB.select(table="staffing", columns=['title'], amount="all")

           # Find the event with the given title
        event_data = next((event for event in events if event.get("title") == title), None)

        if not event_data:
            print(f"Event '{title}' not found in the calendar.")
            return None, None, None, None
        
         # Extract event start and end times
        start_time = event_data.get("start_time")
        end_time = event_data.get("end_time")

        if not start_time:
            print(f"Start time not found for event '{title}'.")
            return None, None, None, None

        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")  # Convert to datetime
        formatted_start_time = start_time.strftime("%H:%M")

        # Handle missing end time (default: 2 hours after start)
        if end_time:
            end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S").strftime("%H:%M")
        else:
            end_time = (start_time + timedelta(hours=2)).strftime("%H:%M")

        # Calculate the new event date based on interval
        today = datetime.today()
        days_until_next = (start_time.weekday() - today.weekday() + interval * 7) % (interval * 7)
        new_date = today + timedelta(days=days_until_next)

        # Get the current scheduled date if staffing exists
        current = None
        if title in [item[0] for item in staffing_exists]:
            current = DB.select(table="staffing", columns=['date'], where=['title'], value={'title': title})[0]

        return new_date, formatted_start_time, end_time, current

    async def _updatemessage(self, id):
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

            dates = await StaffingAsync._geteventdate(self, title, interval)
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

            channel = self.bot.get_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            await message.edit(content=format_staffing_message)

        except Exception as e:
            print(f'Unable to update message - {e}', flush=True)
            raise e

    async def _book(self, ctx, eventDetails, event, usernick, position, section):
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

        time = await StaffingAsync._geteventdate(self, event[1])

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
                if section == None and position.upper() + ':' == pos[1] and pos[2] == '':
                    if int(pos[5]) == 0:
                        request = await Booking.post_booking(self, int(cid), str(date), str(start_time), str(end_time), str(position), int(tag))

                        if request.status_code == requests.codes.ok:
                            feedback = request.json()['booking']
                            DB.update(self=self, table='positions', columns=['user'], values={'user': f'<@{usernick}>'}, where=['position', 'user', 'event'], value={'position': f'{position.upper()}:', 'user': '', 'event': event[0]}, limit=1)
                            
                            selected = DB.select(table="positions", columns=['*'], where=['position', 'user', 'event'], value={'position': f'{position.upper()}:', 'user': f'<@{usernick}>', 'event': event[0]}, amount='all')
                            
                            for select in selected:
                                if select[3] == '':
                                    DB.update(self=self, table='positions', columns=['booking_id'], values={'booking_id': feedback['id']}, where=['id'], value={'id': select[0]})

                            await StaffingAsync._updatemessage(self, event[0])
                            await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{event[1]}`", delete_after=5)
                            booking = True
                        else:
                            await ctx.send(f"<@{usernick}> Booking failed, Control Center responded with error `{request.json()['message']}` code `{request.status_code}`, please try again later", delete_after=5)

                    else:
                        DB.update(self=self, table='positions', columns=['user'], values={'user': f'<@{usernick}>'}, where=['position', 'user', 'event'], value={'position': f'{position.upper()}:', 'user': '', 'event': event[0]}, limit=1)
                        await StaffingAsync._updatemessage(self, event[0])
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


                                await StaffingAsync._updatemessage(self, event[0])
                                await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{event[1]}`", delete_after=5)
                                booking = True
                            else:
                                await ctx.send(f"<@{usernick}> Booking failed, Control Center responded with error `{request.json()['message']}` code `{request.status_code}`, please try again later", delete_after=5)
                    else:
                        DB.update(self=self, table='positions', columns=['user'], values={'user': f'<@{usernick}>'}, where=['position', 'type', 'user', 'event'], value={'position': f'{position.upper()}:', 'type': sections[section], 'user': '', 'event': event[0]}, limit=1)
                        await StaffingAsync._updatemessage(self, event[0])
                        await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{event[1]}`", delete_after=5)
                        booking = True

        if booking == False:
            await ctx.send(f'<@{usernick}> Booking failed, check if you inserted correct postion, section or if the positions is already booked.', delete_after=5)