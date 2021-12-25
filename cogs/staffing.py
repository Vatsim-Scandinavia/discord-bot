import datetime
import asyncio
from aiohttp.client import request

import re
import discord

from discord.ext import commands, tasks
from discord_slash import cog_ext
from requests.api import delete
from helpers.booking import Booking

from helpers.config import GUILD_ID, AVAILABLE_EVENT_DAYS, STAFFING_INTERVAL, VATSCA_BLUE
from helpers.message import staff_roles
from helpers.database import db_connection

guild_id = [GUILD_ID]


class Staffingcog(commands.Cog):
    #
    # ----------------------------------
    # COG FUNCTIONS
    # ----------------------------------
    #

    def __init__(self, bot):
        self.bot = bot
        self.autoreset.start()

    def cog_unload(self):
        self.autoreset.cancel()

    #
    # ----------------------------------
    # SLASH COMMAND FUNCTIONS
    # ----------------------------------
    #
    @cog_ext.cog_slash(name="setupstaffing", guild_ids=guild_id, description="Bot setups staffing information")
    @commands.has_any_role(*staff_roles())
    async def setupstaffing(self, ctx):
        title = await self._get_title(ctx)
        week_int = await self._get_week(ctx)
        date = await self._get_date(ctx, week_int)
        description = await self._get_description(ctx)
        section_1_title = await self._get_first_section(ctx)
        section_2_title = await self._get_second_section(ctx)
        section_3_title = await self._get_third_section(ctx)
        main_position = await self._get_main_positions(ctx, section_1_title)
        secondary_position = await self._get_secondary_positions(ctx, section_2_title)
        regional_position = await self._get_regional_positions(ctx, section_3_title)
        channels = await self._get_channel(ctx)
        
        description = description + "\n\nTo book a position, write `/book`, press TAB and then write the callsign.\nTo unbook a position, use `/unbook`."

        format_staffing_message = ""

        if format_staffing_message != "":
            format_staffing_message += "\n"

        main_position_data = "\n" .join(position for position in main_position)
        secondary_position_data = "\n" .join(
            position for position in secondary_position)
        regional_position_data = "\n" .join(
            position for position in regional_position)

        formatted_date = date.strftime("%A %d/%m/%Y")

        format_staffing_message += f'{title} staffing - {formatted_date}\n\n{description}\n\n{section_1_title}:\n{main_position_data}\n\n{section_2_title}:\n{secondary_position_data}\n\n{section_3_title}:\n{regional_position_data}'

        mydb = db_connection()
        cursor = mydb.cursor()

        for channel in channels:
            msg = await channel.send(format_staffing_message)
            await msg.pin()
            await channel.purge(limit=None, check=lambda msg: not msg.pinned)
            cursor.execute(
                'INSERT INTO staffing(title, date, description, channel_id, message_id, week_interval, main_pos_title, secondary_pos_title, regional_pos_title) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (
                    title,
                    date,
                    description,
                    channel.id,
                    msg.id,
                    week_int,
                    section_1_title,
                    section_2_title,
                    section_3_title
                )
            )

            type = 'main'
            for position in main_position:
                cursor.execute(
                    'INSERT INTO positions(position, user, type, title) VALUES (%s, %s, %s, %s)',
                    (
                        position,
                        "",
                        type,
                        title
                    )
                )

            type = 'secondary'
            for position in secondary_position:
                cursor.execute(
                    'INSERT INTO positions(position, user, type, title) VALUES (%s, %s, %s, %s)',
                    (
                        position,
                        "",
                        type,
                        title
                    )
                )

            type = 'regional'
            for position in regional_position:
                cursor.execute(
                    'INSERT INTO positions(position, user, type, title) VALUES (%s, %s, %s, %s)',
                    (
                        position,
                        "",
                        type,
                        title
                    )
                )
            mydb.commit()

    @cog_ext.cog_slash(name="showallstaffings", guild_ids=guild_id, description="Bot shows all staffings available")
    @commands.has_any_role(*staff_roles())
    async def showallstaffings(self, ctx):
        mydb = db_connection()
        cursor = mydb.cursor()
        cursor.execute(
            'SELECT title FROM staffing'
        )
        showall = cursor.fetchall()
        titels = []
        for each in showall:
            titels.append(each[0])
        showalltitles = "\n" .join(titles for titles in titels)
        await ctx.send(f"All Staffings:\n**`{showalltitles}`**")

    @cog_ext.cog_slash(name="getbookings", guild_ids=guild_id, description="Bot shows all bookings from CC")
    async def getbookings(self, ctx):
        bookings = await Booking.get_bookings(self)
        BookingCallsign = []
        BookingUser = []
        BookingTime = []
        for booking in bookings:
            time_start = datetime.datetime.strptime(booking["time_start"], '%Y-%m-%d %H:%M:%S')
            time_end = datetime.datetime.strptime(booking["time_end"], '%Y-%m-%d %H:%M:%S')
            BookingCallsign.append(booking["callsign"])
            BookingUser.append(booking["name"] + " " + str(booking["cid"]))
            BookingTime.append(time_start.strftime("%d-%m-%Y %H:%M") + " - " + time_end.strftime("%d-%m-%Y %H:%M"))
            
        BookingTimeDisplay = "\n" .join(time for time in BookingTime)
        BookingUserDisplay = "\n" .join(user for user in BookingUser)
        BookingCSDisplay = "\n" .join(callsign for callsign in BookingCallsign)

        if len(BookingCallsign) == 0:
            BookingTimeDisplay = "No bookings found"
            BookingUserDisplay = "No bookings found"
            BookingCSDisplay = "No bookings found"

        embedVar = discord.Embed(title="All active bookings in CC", description="This is all active bookings there is stored in CC", color=VATSCA_BLUE)
        embedVar.add_field(name="Callsign", value=BookingCSDisplay, inline=True)
        embedVar.add_field(name="User", value=BookingUserDisplay, inline=True)
        embedVar.add_field(name="Start and end time", value=BookingTimeDisplay, inline=True)
        await ctx.send(embed=embedVar)

    @cog_ext.cog_slash(name="manreset", guild_ids=guild_id, description="Bot manually resets specific staffing")
    @commands.has_any_role(*staff_roles())
    async def man_reset(self, ctx, title):
        await self.bot.wait_until_ready()
        mydb = db_connection()
        cursor = mydb.cursor()
        cursor.execute('SELECT * FROM staffing WHERE title = %s', (title,))
        staffing = cursor.fetchone()
        date = staffing[2]
        week = staffing[6]
        day = date.strftime("%d")
        month = date.strftime("%m")
        year = date.strftime("%Y")
        formatted_date = datetime.datetime(int(year), int(month), int(day))
        cursor.execute("UPDATE positions SET user = %s WHERE title = %s", ("", title))
        newdate = None
        times = 7
        i = -1
        w = week
        for _ in range(int(times)):
            i += 1
            if formatted_date.weekday() == i:
                today = datetime.date.today()
                newdate = today + \
                    datetime.timedelta(days=i-today.weekday(), weeks=int(w))

                cursor.execute("UPDATE staffing SET date = %s WHERE title = %s", (newdate, title))
                mydb.commit()
                await self._updatemessage(title)
                channel = self.bot.get_channel(int(staffing[4]))
                await channel.send("The chat is being manually reset!")
                await asyncio.sleep(5)
                await channel.purge(limit=None, check=lambda msg: not msg.pinned)

    @cog_ext.cog_slash(name="updatestaffing", guild_ids=guild_id, description='Bot updates selected staffing')
    @commands.has_any_role(*staff_roles())
    async def updatestaffing(self, ctx, title):
        try:
            mydb = db_connection()
            cursor = mydb.cursor()
            cursor.execute(
                'SELECT title FROM staffing'
            )
            showall = cursor.fetchall()
            titles = []
            for all in showall:
                titles.append(all[0])

            if title in titles:
                options = ['Title', 'Day of event', 'Staffing message', 'First Section',
                           'Second Section', 'Third Section', 'Delete Staffing', 'Exit Updater']
                avail = "\n" .join(files for files in options)
                await ctx.send(f'What would you like to update in staffing `{title}`? **FYI this command expires in 1 minute**\n\nAvailable options:\n{avail}')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

                if message.content == options[0]:
                    newtitle = await self._get_title(ctx)
                    cursor.execute("UPDATE staffing, positions SET staffing.title = %s, positions.title = %s WHERE staffing.title = %s and positions.title = %s", (newtitle, newtitle, title, title))
                    mydb.commit()
                    title = newtitle
                    await self._updatemessage(title)
                    await ctx.send(f'Title updated to - {title}')

                elif message.content == options[1]:
                    week_int = await self._get_week(ctx)
                    newdate = await self._get_date(ctx, week_int)
                    cursor.execute("UPDATE staffing SET date = %s, week_interval = %s WHERE title = %s", (newdate, week_int, title))
                    mydb.commit()
                    await self._updatemessage(title)
                    formatted_date = newdate.strftime("%A %d/%m/%Y")
                    await ctx.send(f'Event date has been updated to - `{formatted_date}` & Week interval updated to - `{week_int}`')

                elif message.content == options[2]:
                    newdescription = await self._get_description(ctx)
                    newdescription = newdescription + "\n\nTo book a position, write `/book`, press TAB and then write the callsign.\nTo unbook a position, use `/unbook`."

                    cursor.execute("UPDATE staffing SET description = %s WHERE title = %s", (newdescription, title))
                    mydb.commit()
                    await self._updatemessage(title)
                    await ctx.send(f'Event description/staffing message has been updated to:\n{newdescription}')

                elif message.content == options[3]:
                    first_section = await self._get_first_section(ctx)
                    new_main_positions = await self._get_main_positions(ctx, first_section)
                    formatted_main_positions = "\n" .join(
                        position for position in new_main_positions)
                    cursor.execute("UPDATE staffing SET main_pos_title = %s WHERE title = %s", (first_section, title))
                    type = 'main'
                    cursor.execute(
                        "DELETE FROM positions WHERE type = %s and title = %s", (type, title))
                    for position in new_main_positions:
                        cursor.execute('INSERT INTO positions(position, user, type, title) VALUES (%s, %s, %s, %s)',
                                       (
                                           position,
                                           "",
                                           type,
                                           title
                                       ))
                    mydb.commit()
                    await self._updatemessage(title)
                    await ctx.send(f'Main Positions updated to:\n{formatted_main_positions}\n\nFirst Section Title updated to `{first_section}`')

                elif message.content == options[4]:
                    second_section = await self._get_second_section(ctx)
                    new_secondary_positions = await self._get_secondary_positions(ctx, second_section)
                    formatted_secondary_positions = "\n" .join(
                        position for position in new_secondary_positions)
                    cursor.execute("UPDATE staffing SET secondary_pos_title = %s WHERE title = %s", (second_section, title))
                    type = 'secondary'
                    cursor.execute("DELETE FROM positions WHERE type = %s and title = %s", (type, title))
                    for position in new_secondary_positions:
                        cursor.execute('INSERT INTO positions(position, user, type, title) VALUES (%s, %s, %s, %s)',
                                       (
                                           position,
                                           "",
                                           type,
                                           title
                                       ))
                    mydb.commit()
                    await self._updatemessage(title)
                    await ctx.send(f'Secondary Positions updated to:\n{formatted_secondary_positions}\n\nSecond Section Title updated to `{second_section}`')

                elif message.content == options[5]:
                    third_section = await self._get_third_section(ctx)
                    new_regional_positions = await self._get_regional_positions(ctx, third_section)
                    formatted_regional_positions = "\n" .join(
                        position for position in new_regional_positions)
                    cursor.execute("UPDATE staffing SET regional_pos_title = %s WHERE title = %s", (third_section, title))
                    type = 'regional'
                    cursor.execute("DELETE FROM positions WHERE type = %s and title = %s", (type, title))
                    for position in new_regional_positions:
                        cursor.execute('INSERT INTO positions(position, user, type, title) VALUES (%s, %s, %s, %s)',
                                       (
                                           position,
                                           "",
                                           type,
                                           title
                                       ))
                    mydb.commit()
                    await self._updatemessage(title)
                    await ctx.send(f'Regional Positions updated to:\n{formatted_regional_positions}\n\nThird Section Title updated to `{third_section}`')

                elif message.content == options[6]:
                    confirm_delete = await self._getconfirmation(ctx, title)

                    if confirm_delete == title:
                        cursor.execute("SELECT * FROM staffing WHERE title = %s", (title,))
                        all_details = cursor.fetchone()
                        channel_id = all_details[4]
                        message_id = all_details[5]
                        channel = self.bot.get_channel(int(channel_id))
                        message = await channel.fetch_message(int(message_id))
                        await message.delete()
                        cursor.execute("DELETE FROM staffing WHERE title = %s", (title,))
                        cursor.execute("DELETE FROM positions WHERE title = %s", (title,))
                        mydb.commit()

                        await ctx.send(f'Staffing for `{title}` has been deleted')
                    elif confirm_delete == 'CANCEL':
                        await ctx.send(f'Deletion of `{title}` has been cancelled.')

                elif message.content == options[7]:
                    now = datetime.datetime.now()
                    now = now.strftime("%d-%m-%Y %H:%M:%S %p")
                    await ctx.send(f'Staffing updater for `{title}` exited at - {now}')
            else:
                await ctx.send(f'{title} staffing does not exist.')
        except Exception as e:
            await ctx.send(f'Error updating staffing {title} - {e}')
            raise e

    @cog_ext.cog_slash(name="book", guild_ids=guild_id, description='Bot books selected position for selected staffing')
    async def book(self, ctx, position):
        try:
            mydb = db_connection()
            cursor = mydb.cursor()

            cursor.execute("SELECT channel_id FROM staffing")
            event_channel = cursor.fetchall()
            
            cursor.execute("SELECT title FROM staffing WHERE channel_id = %s", (ctx.channel_id,))
            title = cursor.fetchone()

            cursor.execute("SELECT position, user FROM positions WHERE title = %s", (title[0],))
            positions = cursor.fetchall()

            cursor.execute("SELECT date FROM staffing WHERE title = %s", (title[0],))
            eventDetails = cursor.fetchone()

            usernick = ctx.author.id
            if any(ctx.channel_id in channel for channel in event_channel):
                if any(f'<@{usernick}>' in match for match in positions):
                    await ctx.send(f"<@{usernick}> You already have a booking!", delete_after=5)
                elif any(position.upper() + ':' in match for match in positions):
                    cid = re.findall("\d+", str(ctx.author.nick))[0]
                    
                    cursor.execute("SELECT start_time FROM events WHERE name = %s", (title[0],))
                    start = cursor.fetchone()
                    start_formatted = datetime.datetime.strptime(str(start[0]), '%Y-%m-%d %H:%M:%S')
                    start_time = start_formatted.strftime("%H:%M")

                    end_formatted = start_formatted + datetime.timedelta(hours=2)
                    end_time = end_formatted.strftime("%H:%M")

                    tag = 3

                    date = datetime.datetime.strptime(str(eventDetails[0]), '%Y-%m-%d')
                    date = date.strftime("%d/%m/%Y")

                    request = await Booking.post_booking(self, int(cid), str(date), str(start_time), str(end_time), str(position), int(tag))

                    if request == 200:
                        cursor.execute("UPDATE positions SET user = %s WHERE position = %s and title = %s", (f'<@{usernick}>', f'{position.upper()}:', title[0]))
                        mydb.commit()

                        await self._updatemessage(title[0])
                        await ctx.send(f"<@{usernick}> Confirmed booking for position `{position.upper()}` for event `{title[0]}`", delete_after=5)
                    else:
                        await ctx.send(f"<@{usernick}> Booking failed, Control Center responded with error {request}, please try again later", delete_after=5)
                else:
                    await ctx.send(f"<@{usernick}> The bot could not find the position you tried to book.")
            else:
                await ctx.send(f"<@{usernick}> Please use the correct channel", delete_after=5)

        except Exception as e:
            await ctx.send(f"Error booking position {position} - {e}")
            raise e

    @cog_ext.cog_slash(name="unbook", guild_ids=guild_id, description='Bot books selected position for selected staffing')
    async def unbook(self, ctx):
        try:
            mydb = db_connection()
            cursor = mydb.cursor()

            cursor.execute("SELECT channel_id FROM staffing")
            event_channel = cursor.fetchall()
            
            cursor.execute("SELECT title FROM staffing WHERE channel_id = %s", (ctx.channel_id,))
            title = cursor.fetchone()

            cursor.execute("SELECT position, user FROM positions WHERE title = %s", (title[0],))
            positions = cursor.fetchall()

            usernick = ctx.author.id
            if any(ctx.channel_id in channel for channel in event_channel):
                if any(f'<@{usernick}>' in match for match in positions):

                    cid = re.findall("\d+", str(ctx.author.nick))[0]

                    cursor.execute("SELECT position FROM positions WHERE user = %s and title = %s", (f'<@{usernick}>', title[0]))
                    position = cursor.fetchone()

                    request = await Booking.delete_booking(self, int(cid), str(position[0]))
                    if request == 200:
                        cursor.execute("UPDATE positions SET user = %s WHERE user = %s and title = %s", ("", f'<@{usernick}>', title[0]))
                        mydb.commit()
                        await self._updatemessage(title[0])
                        await ctx.send(f"<@{usernick}> Confirmed cancelling of your booking!", delete_after=5)
                    else:
                        await ctx.send(f"<@{usernick}> Cancelling failed, Control Center responded with error {request}, please try again later", delete_after=5)
            else:
                await ctx.send(f"<@{usernick}> Please use the correct channel", delete_after=5)
        except Exception as e:
            await ctx.send(f"Error unbooking position for event {title[0]} - {e}")
            raise e

    #
    # ----------------------------------
    # TASK LOOP FUNCTIONS
    # ----------------------------------
    #
    @tasks.loop(seconds=STAFFING_INTERVAL)
    async def autoreset(self):
        await self.bot.wait_until_ready()
        mydb = db_connection()
        cursor = mydb.cursor()
        cursor.execute('SELECT * FROM staffing')
        staffings = cursor.fetchall()
        now = datetime.datetime.utcnow()

        for staffing in staffings:
            date = staffing[2]
            week = staffing[6]
            day = date.strftime("%d")
            month = date.strftime("%m")
            year = date.strftime("%Y")
            formatted_date = datetime.datetime(int(year), int(month), int(day))

            if now.date() == formatted_date.date() and now.hour == 21 and 0 <= now.minute <= 5:
                title = staffing[1]
                cursor.execute("UPDATE positions SET user = %s WHERE title = %s", ("", title))
                newdate = None
                times = 7
                i = -1
                w = week
                for _ in range(int(times)):
                    i += 1
                    if formatted_date.weekday() == i:
                        today = datetime.date.today()
                        newdate = today + \
                            datetime.timedelta(days=i-today.weekday(), weeks=int(w))

                cursor.execute("UPDATE staffing SET date = %s WHERE title = %s", (newdate, title))
                mydb.commit()
                await self._updatemessage(title)
                channel = self.bot.get_channel(int(staffing[4]))
                await channel.send("The chat is being automatic reset!")
                await asyncio.sleep(5)
                await channel.purge(limit=None, check=lambda msg: not msg.pinned)

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
            await ctx.send('Event Title? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            mydb = db_connection()
            cursor = mydb.cursor()
            cursor.execute(
                'SELECT title FROM staffing'
            )
            getall = cursor.fetchall()
            for each in getall:
                if message.content == each[0]:
                    await ctx.send(f'The event `{message.content}` already exists.')
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
            times = await self.get_howmanypositions(ctx, type)
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
            times = await self.get_howmanypositions(ctx, type)
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
            times = await self.get_howmanypositions(ctx, type)
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

    async def _updatemessage(self, title):
        try:
            mydb = db_connection()
            cursor = mydb.cursor()
            cursor.execute("SELECT * FROM staffing WHERE title = %s", (title,))

            events = cursor.fetchone()

            title = events[1]
            date = events[2]
            description = events[3]
            channel_id = events[4]
            message_id = events[5]
            first_section = events[7]
            second_section = events[8]
            third_section = events[9]

            type = 'main'
            cursor.execute(
                "SELECT * FROM positions WHERE title = %s and type = %s", (title, type))
            main_pos = cursor.fetchall()
            main_positions = []
            for position in main_pos:
                main_positions.append(f'{position[1]} {position[2]}')
                main_position_data = "\n" .join(
                    position for position in main_positions)

            type = 'secondary'
            cursor.execute(
                "SELECT * FROM positions WHERE title = %s and type = %s", (title, type))
            secondary_pos = cursor.fetchall()
            secondary_positions = []
            for position in secondary_pos:
                secondary_positions.append(f'{position[1]} {position[2]}')
                secondary_position_data = "\n" .join(
                    position for position in secondary_positions)

            type = 'regional'
            cursor.execute(
                "SELECT * FROM positions WHERE title = %s and type = %s", (title, type))
            regional_pos = cursor.fetchall()
            regional_positions = []
            for position in regional_pos:
                regional_positions.append(f'{position[1]} {position[2]}')
                regional_position_data = "\n" .join(
                    position for position in regional_positions)

            format_staffing_message = ""

            if format_staffing_message != "":
                format_staffing_message += "\n"

            formatted_date = date.strftime("%A %d/%m/%Y")
            format_staffing_message += f'{title} staffing - {formatted_date}\n\n{description}\n\n{first_section}:\n{main_position_data}\n\n{second_section}:\n{secondary_position_data}\n\n{third_section}:\n{regional_position_data}'

            channel = self.bot.get_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            await message.edit(content=format_staffing_message)

        except Exception as e:
            print(f'Unable to update message - {e}')
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

def setup(bot):
    bot.add_cog(Staffingcog(bot))
