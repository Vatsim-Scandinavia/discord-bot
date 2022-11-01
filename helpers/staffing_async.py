import re
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
        for staffing in staffings:
            formatted_staffings.append(" ".join(map(str, staffing)))

        formatted_events = []
        for event in events:
            formatted_event = " ".join(map(str, event))
            if formatted_event not in formatted_staffings:
                formatted_events.append(formatted_event)

        return Literal[tuple(formatted_events)]

    async def _get_title(self, ctx):
        """
        Function gets the title from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Event Title? Note: This title has to be identical to the event from the Calendar **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            getall = StaffingDB.select(self=self, table='staffing', columns=[
                                       'title'], amount='all')
            for each in getall:
                if message.content == each[0]:
                    await ctx.send(f'The event `{message.content}` already exists.')
                    raise ValueError

            realEvents = StaffingDB.select(
                self=self, table='events', columns=['name'], amount='all')
            allEvents = []
            for each in realEvents:
                allEvents.append(each[0])
            if message.content not in allEvents:
                await ctx.send(f'The event `{message.content}` does not exists.')
                raise ValueError

            return message.content
        except Exception as e:
            await ctx.send(f'Error getting the title - {e}')
            raise e

    async def _get_date(self, ctx, week_int):
        """
        Function gets the date of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            avail_days = AVAILABLE_EVENT_DAYS

            await ctx.send('Event Day of the week? **FYI this command expires in 1 minute** Available days: ' + str(avail_days)[1:-1])
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            times = 7
            i = -1
            w = int(week_int)
            for _ in range(int(times)):
                i += 1
                if message.content == avail_days[i]:
                    today = datetime.date.today()
                    event_day = today + \
                        datetime.timedelta(days=i-today.weekday(), weeks=w)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return event_day
        except Exception as e:
            await ctx.send(f'Error getting date of the event - {e}')
            raise e

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

    async def _geteventdate(self, title):
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
        days = (start.weekday() - today.weekday() + 7) % 7
        newdate = today + timedelta(days=days)
        return newdate, start_time, end_time

    async def _updatemessage(self, title):
        try:
            events = StaffingDB.select(self=self, table='staffing', columns=[
                                       '*'], where=['title'], value={'title': title})

            title = events[1]
            date = events[2]
            description = events[3]
            channel_id = events[4]
            message_id = events[5]
            first_section = events[7]
            second_section = events[8]
            third_section = events[9]

            time = await StaffingAsync._geteventdate(self, title)
            start_time = time[0]
            end_time = time[1]

            i = 0

            

        except Exception as e:
            print(f'Unable to update message - {e}')
            raise e

    async def _book(self, ctx, eventDetails, title, usernick, position):
        cid = re.findall("\d+", str(ctx.author.nick))[0]

        time = await StaffingAsync._geteventtime(self, title[0])
        start_time = time[0]
        end_time = time[1]

        tag = 3

        date = datetime.datetime.strptime(str(eventDetails[0]), '%Y-%m-%d')
        date = date.strftime("%d/%m/%Y")

        request = await Booking.post_booking(self, int(cid), str(date), str(start_time), str(end_time), str(position), int(tag))

        if request == 200:
            StaffingDB.update(self=self, table='positions', columns=['user'], values={
                              'user': f'<@{usernick}>'}, where=['position', 'title'], value={'position': f'{position.upper()}:', 'title': title[0]})

            await self._updatemessage(title[0])
            await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{title[0]}`", delete_after=5)
        else:
            await ctx.send(f"<@{usernick}> Booking failed, Control Center responded with error `{request.json()['message']}` code `{request.status_code}`, please try again later", delete_after=5)
