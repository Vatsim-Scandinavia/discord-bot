import re
import discord
from typing import Literal

from datetime import datetime, timedelta

from helpers.booking import Booking

from helpers.config import AVAILABLE_EVENT_DAYS
from helpers.database import db_connection
from helpers.staffing_db import StaffingDB


class StaffingAsync():

    def __init__(self) -> None:
        pass

    #
    # ----------------------------------
    # ASYNC DATA FUNCTIONS
    # ----------------------------------
    #
    def _get_titles() -> Literal:
        events = StaffingDB.select(table='events', columns=[
                                   'name'], amount='all')
        staffings = StaffingDB.select(
            table="staffing", columns=['title'], amount='all')
        formatted_staffings = []
        formatted_events = []

        if not events:
            formatted_events.append('None is available. Please try again later.')
        else:
            for staffing in staffings:
                formatted_staffings.append(" ".join(map(str, staffing)))

            for event in events:
                formatted_event = " ".join(map(str, event))
                if formatted_event not in formatted_staffings:
                    formatted_events.append(formatted_event)
        return Literal[tuple(formatted_events)]

    def _get_avail_titles() -> Literal:
        staffings = StaffingDB.select(table="staffing", columns=['title'], amount='all')
        formatted_staffings = []
        if not staffings:
            formatted_staffings.append('None is available. Please try again later.')
        else:
            for staffing in staffings:
                formatted_staffings.append(" ".join(map(str, staffing)))

        return Literal[tuple(formatted_staffings)]
        
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
            await ctx.send('Should the event have booking restriction? Allwed ansers: `Yes` or `No` **FYI this command expires in 5 minutes**')
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
            position = []
            times = await StaffingAsync.get_howmanypositions(self, ctx, title)

            i = 1
            for _ in range(int(times)):
                await ctx.send(f'{title} nr. {i}? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)
                position.append(message.content + ':')
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
        start = StaffingDB.select(table="events", columns=["start_time"], where=[
                                  "name"], value={'name': title})[0]
        start_time = start.strftime("%H:%M")

        end = StaffingDB.select(table='events', columns=['end_time'], where=[
                                'name'], value={'name': title})[0]
        if end is not None:
            end_time = end.strftime("%H:%M")
        else:
            end_formatted = start + timedelta(hours=2)
            end_time = end_formatted.strftime("%H:%M")
        today = datetime.today()
        days = (start.weekday() - today.weekday() + 7) % (interval * 7)
        newdate = today + timedelta(days=days)
        current = StaffingDB.select(table="staffing", columns=['date'], where=['title'], value={'title' : title})[0]
        return newdate, start_time, end_time, current

    async def _updatemessage(self, title):
        try:
            event = StaffingDB.select(table='staffing', columns=['*'], where=['title'], value={'title': title})

            title = event[1]
            description = event[3]
            channel_id = event[4]
            message_id = event[5]
            first_section = event[7]
            second_section = event[8]
            third_section = event[9]

            dates = await StaffingAsync._geteventdate(self, title)
            start_time = dates[1]
            end_time = dates[2]

            format_staffing_message = ""

            if format_staffing_message != "":
                format_staffing_message += "\n"

            formatted_date = dates[3].strftime('%A %d/%m/%Y')

            section_positions = {}
            section_positions[first_section] = StaffingDB.select(table='positions', columns=['*'], where=['title', 'type'], value={'title': title, 'type': 1}, amount='all')
            section_positions[second_section] = StaffingDB.select(table='positions', columns=['*'], where=['title', 'type'], value={'title': title, 'type': 2}, amount='all')
            section_positions[third_section] = StaffingDB.select(table='positions', columns=['*'], where=['title', 'type'], value={'title': title, 'type': 3}, amount='all')

            pos_info = ''
            for x in section_positions:
                if x is not None:
                    pos_data = []
                    for pos in section_positions[x]:
                        pos_data.append(f'{pos[1]} {pos[2]}')
                    pos_info += f'\n\n{x}:\n' + '\n' .join(position for position in pos_data)
                
            format_staffing_message += f'{title} staffing - {formatted_date} {start_time} - {end_time}z\n\n{description}{pos_info}'

            channel = self.bot.get_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            await message.edit(content=format_staffing_message)

        except Exception as e:
                print(f'Unable to update message - {e}')
                raise e

    async def _book(self, ctx, eventDetails, title, usernick, position):
        cid = re.findall("\d+", str(ctx.author.nick))[0]

        time = await StaffingAsync._geteventdate(self, title[0])
        start_time = time[1]
        end_time = time[2]

        tag = 3

        date = datetime.strptime(str(eventDetails[0]), '%Y-%m-%d')
        date = date.strftime("%d/%m/%Y")

        request = await Booking.post_booking(self, int(cid), str(date), str(start_time), str(end_time), str(position), int(tag))

        if request == 200:
            StaffingDB.update(self=self, table='positions', columns=['user'], values={
                              'user': f'<@{usernick}>'}, where=['position', 'title'], value={'position': f'{position.upper()}:', 'title': title[0]})

            await StaffingAsync._updatemessage(self, title[0])
            await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{title[0]}`", delete_after=5)
        else:
            await ctx.send(f"<@{usernick}> Booking failed, Control Center responded with error `{request.json()['message']}` code `{request.status_code}`, please try again later", delete_after=5)
