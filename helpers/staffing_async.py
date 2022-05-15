import datetime
import re
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

            getall = StaffingDB.select(self=self, table='staffing', columns=['title'], amount='all')
            for each in getall:
                if message.content == each[0]:
                    await ctx.send(f'The event `{message.content}` already exists.')
                    raise ValueError

            realEvents = StaffingDB.select(self=self, table='events', columns=['name'], amount='all')
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

    async def _get_week(self, ctx):
        """
        Function gets the week interval the day of the event is in.
        :param ctx:
        :return:
        """
        try:
            await ctx.send(f'What is the week interval of the event? If reply is `1` the date will be selected each week. if reply is `2` then its each second week and so on. **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content

        except Exception as e:
            await ctx.send(f'Error getting date of the event - {e}')
            raise

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

    async def _get_first_section(self, ctx):
        """
        Function gets the title for positions of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            await ctx.send('First section title? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as e:
            await ctx.send(f'Error getting the first section title - {e}')
            raise e

    async def _get_second_section(self, ctx):
        """
        Function gets the title for positions of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Second section title? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as e:
            await ctx.send(f'Error getting the second section title - {e}')
            raise e

    async def _get_third_section(self, ctx):
        """
        Function gets the title for positions of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Third section title? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as e:
            await ctx.send(f'Error getting the third section title - {e}')
            raise e

    async def _get_main_positions(self, ctx, first_section):
        """
        Function gets the main positions of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            position = []
            type = 'Main'
            times = await StaffingAsync.get_howmanypositions(self, ctx, type)
            num = 0
            for _ in range(int(times)):
                num += 1
                await ctx.send(f'{first_section} nr. {num}? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)
                position.append(message.content + ':')

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No positions was provided.')
                raise ValueError

            return position
        except Exception as e:
            await ctx.send(f'Error getting {first_section} - {e}')
            raise e

    async def _get_secondary_positions(self, ctx, second_section):
        """
        Function gets the main positions of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            position = []
            type = 'Secondary'
            times = await StaffingAsync.get_howmanypositions(self, ctx, type)
            num = 0
            for _ in range(int(times)):
                num += 1
                await ctx.send(f'{second_section} nr. {num}? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)
                position.append(message.content + ':')

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No positions was provided.')
                raise ValueError

            return position
        except Exception as e:
            await ctx.send(f'Error getting {second_section} - {e}')
            raise e

    async def _get_regional_positions(self, ctx, third_section):
        """
        Function gets the main positions of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            position = []
            type = 'Regional'
            times = await StaffingAsync.get_howmanypositions(self, ctx, type)
            num = 0
            for _ in range(int(times)):
                num += 1
                await ctx.send(f'{third_section} nr. {num}? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)
                position.append(message.content + ':')

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No positions was provided.')
                raise ValueError

            return position
        except Exception as e:
            await ctx.send(f'Error getting {third_section} - {e}')
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

    async def _get_restrict_positions(self, ctx):
        """
        Function gets if the signup should restrict signups to primary pos only until fully booked
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Should signups be restricted to primary positions only? **FYI this command expires in 1 minute** (yes/no)')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            if(message.content.lower() == 'yes'):
                return 1
            elif(message.content.lower() == 'no'):
                return 0
            else:
                await ctx.send('Setup cancelled. Wrong format provided.')
                raise ValueError
            
        except Exception as e:
            await ctx.send(f'Error getting the restrict positions - {e}')
            raise e

    async def _get_channel(self, ctx):
        """
        Function gets the channel of the event from a message where the staffing message will be posted
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Where would you like to post the staffing message? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.channel_mentions) < 1:
                await ctx.send('Setup canceled. No channel provided.')
                raise ValueError

            return message.channel_mentions
        except Exception as e:
            await ctx.send(f'Error getting channel - {e}')
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

    async def _geteventtime(self, title):
        start = StaffingDB.select(self=self, table='events', columns=['start_time'], where=['name'], value={'name': title})
        start_formatted = datetime.datetime.strptime(str(start[0]), '%Y-%m-%d %H:%M:%S')
        start_time = start_formatted.strftime("%H:%M")

        end = StaffingDB.select(self=self, table='events', columns=['end_time'], where=['name'], value={'name': title})
        if end[0] is not None:
            end_formatted = datetime.datetime.strptime(str(end[0]), '%Y-%m-%d %H:%M:%S')
            end_time = end_formatted.strftime("%H:%M")
        else:
            end_formatted = start_formatted + datetime.timedelta(hours=2)
            end_time = end_formatted.strftime("%H:%M")

        return start_time, end_time

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
            StaffingDB.update(self=self, table='positions', columns=['user'], values={'user': f'<@{usernick}>'}, where=['position', 'title'], value={'position': f'{position.upper()}:', 'title': title[0]})

            await self._updatemessage(title[0])
            await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{title[0]}`", delete_after=5)
        else:
            await ctx.send(f"<@{usernick}> Booking failed, Control Center responded with error `{request.json()['message']}` code `{request.status_code}`, please try again later", delete_after=5)

