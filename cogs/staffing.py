import datetime
import asyncio

import re
import discord

from discord.ext import commands, tasks
from discord_slash import cog_ext
from helpers.booking import Booking

from helpers.config import GUILD_ID, STAFFING_INTERVAL, VATSCA_BLUE, VATSIM_MEMBER_ROLE, VATSCA_MEMBER_ROLE, OBS_RATING_ROLE
from helpers.message import staff_roles
from helpers.database import db_connection
from helpers.staffing_async import StaffingAsync
from helpers.staffing_db import StaffingDB

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
        title = await StaffingAsync._get_title(self, ctx)
        week_int = await StaffingAsync._get_week(self, ctx)
        date = await StaffingAsync._get_date(self, ctx, week_int)
        description = await StaffingAsync._get_description(self, ctx)
        section_1_title = await StaffingAsync._get_first_section(self, ctx)
        section_2_title = await StaffingAsync._get_second_section(self, ctx)
        section_3_title = await StaffingAsync._get_third_section(self, ctx)
        main_position = await StaffingAsync._get_main_positions(self, ctx, section_1_title)
        secondary_position = await StaffingAsync._get_secondary_positions(self, ctx, section_2_title)
        regional_position = await StaffingAsync._get_regional_positions(self, ctx, section_3_title)
        restrict_booking = await StaffingAsync._get_restrict_positions(self, ctx)
        channels = await StaffingAsync._get_channel(self, ctx)
        
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

        time = await StaffingAsync._geteventtime(self, title)
        start_time = time[0]
        end_time = time[1]

        format_staffing_message += f'{title} staffing - {formatted_date} {start_time} - {end_time}z\n\n{description}\n\n{section_1_title}:\n{main_position_data}\n\n{section_2_title}:\n{secondary_position_data}\n\n{section_3_title}:\n{regional_position_data}'

        for channel in channels:
            msg = await channel.send(format_staffing_message)
            await msg.pin()
            await channel.purge(limit=None, check=lambda msg: not msg.pinned)
            StaffingDB.insert(self=self, table='staffing', columns=['title', 'date', 'description', 'channel_id', 'message_id', 'week_interval', 'main_pos_title', 'secondary_pos_title', 'regional_pos_title', 'restrict_bookings'], values=[str(title), str(date), str(description), str(channel.id), str(msg.id), str(week_int), str(section_1_title), str(section_2_title), str(section_3_title), str(restrict_booking)])

            type = 'main'
            for position in main_position:
                StaffingDB.insert(self=self, table='positions', columns=['position', 'user', 'type', 'title'], values=[position, "", type, title])

            type = 'secondary'
            for position in secondary_position:
                StaffingDB.insert(self=self, table='positions', columns=['position', 'user', 'type', 'title'], values=[position, "", type, title])

            type = 'regional'
            for position in regional_position:
                StaffingDB.insert(self=self, table='positions', columns=['position', 'user', 'type', 'title'], values=[position, "", type, title])

    @cog_ext.cog_slash(name="showallstaffings", guild_ids=guild_id, description="Bot shows all staffings available")
    @commands.has_any_role(*staff_roles())
    async def showallstaffings(self, ctx):
        showall = StaffingDB.select(self=self, table='staffing', columns=['title'], amount='all')
        titels = []
        for each in showall:
            titels.append(each[0])
        showalltitles = "\n" .join(titles for titles in titels)
        embed = discord.Embed(title="All staffings", description='This displays all staffings currently available', color=VATSCA_BLUE)
        embed.add_field(name="Staffings", value=showalltitles, inline=True)
        await ctx.send(embed=embed)

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
    async def man_reset(self, title):
        await self.bot.wait_until_ready()
        staffing = StaffingDB.select(self=self, table='staffing', columns=['*'], where=['title'], value={'title': title})
        date = staffing[2]
        week = staffing[6]
        day = date.strftime("%d")
        month = date.strftime("%m")
        year = date.strftime("%Y")
        formatted_date = datetime.datetime(int(year), int(month), int(day))
        values = { 'user': '', }
        StaffingDB.update(self=self, table='positions', where=['title'], value={'title': title}, columns=['user'], values=values)
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
                values = { 'date': newdate, }
                StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': title}, columns=['date'], values=values)
                await self._updatemessage(title)
                channel = self.bot.get_channel(int(staffing[4]))
                await channel.send("The chat is being manually reset!")
                await asyncio.sleep(5)
                await channel.purge(limit=None, check=lambda msg: not msg.pinned)

    @cog_ext.cog_slash(name="updatestaffing", guild_ids=guild_id, description='Bot updates selected staffing')
    @commands.has_any_role(*staff_roles())
    async def updatestaffing(self, ctx, title):
        try:
            showall = StaffingDB.select(self=self, table='staffing', columns=['title'], amount='all')
            titles = []
            for all in showall:
                titles.append(all[0])

            if title in titles:
                options = ['1. Title', '2. Day of event', '3. Staffing message', '4. First Section',
                           '5. Second Section', '6. Third Section', '7. Change booking restriction', '8. Delete Staffing', '9. Exit Updater']
                avail = "\n" .join(files for files in options)
                await ctx.send(f'What would you like to update in staffing `{title}`? **FYI this command expires in 1 minute**\n\nAvailable options:\n{avail}')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

                if message.content == '1':
                    newtitle = await StaffingAsync._get_title(self, ctx)
                    values = { 'title': newtitle, }
                    StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': title}, columns=['title'], values=values)
                    title = newtitle
                    await self._updatemessage(title)
                    await ctx.send(f'Title updated to - {title}')

                elif message.content == '2':
                    week_int = await StaffingAsync._get_week(self, ctx)
                    newdate = await StaffingAsync._get_date(self, ctx, week_int)
                    values = { 'date': newdate, 'week_interval': week_int, }
                    StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': title}, columns=['date', 'week_interval'], values=values)
                    await self._updatemessage(title)
                    formatted_date = newdate.strftime("%A %d/%m/%Y")
                    await ctx.send(f'Event date has been updated to - `{formatted_date}` & Week interval updated to - `{week_int}`')

                elif message.content == '3':
                    newdescription = await StaffingAsync._get_description(self, ctx)
                    newdescription = newdescription + "\n\nTo book a position, write `/book`, press TAB and then write the callsign.\nTo unbook a position, use `/unbook`."

                    values = { 'description': newdescription, }
                    StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': title}, columns=['description'], values=values)
                    await self._updatemessage(title)
                    await ctx.send(f'Event description/staffing message has been updated to:\n{newdescription}')

                elif message.content == '4':
                    first_section = await StaffingAsync._get_first_section(self, ctx)
                    new_main_positions = await StaffingAsync._get_main_positions(self, ctx, first_section)
                    formatted_main_positions = "\n" .join(
                        position for position in new_main_positions)
                    
                    values = { 'main_pos_title': formatted_main_positions, }
                    StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': title}, columns=['main_pos_title'], values=formatted_main_positions)
                    type = 'main'
                    value = { 'type' : type, 'title' : title, }
                    StaffingDB.delete(self=self, table='positions', where=['type', 'title'], value=value)
                    for position in new_main_positions:
                        await StaffingDB.insert_positions(self, position, '', type, title)
                    await self._updatemessage(title)
                    await ctx.send(f'Main Positions updated to:\n{formatted_main_positions}\n\nFirst Section Title updated to `{first_section}`')

                elif message.content == '5':
                    second_section = await StaffingAsync._get_second_section(self, ctx)
                    new_secondary_positions = await StaffingAsync._get_secondary_positions(self, ctx, second_section)
                    formatted_secondary_positions = "\n" .join(
                        position for position in new_secondary_positions)
                    values = { 'secondary_pos_title': formatted_secondary_positions, }
                    StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': title}, columns=['secondary_pos_title'], values=formatted_secondary_positions)
                    type = 'secondary'
                    value = { 'type' : type, 'title' : title, }
                    StaffingDB.delete(self=self, table='positions', where=['type', 'title'], value=value)
                    for position in new_secondary_positions:
                        await StaffingDB.insert_positions(self, position, '', type, title)
                    await self._updatemessage(title)
                    await ctx.send(f'Secondary Positions updated to:\n{formatted_secondary_positions}\n\nSecond Section Title updated to `{second_section}`')

                elif message.content == '6':
                    third_section = await StaffingAsync._get_third_section(self, ctx)
                    new_regional_positions = await StaffingAsync._get_regional_positions(self, ctx, third_section)
                    formatted_regional_positions = "\n" .join(
                        position for position in new_regional_positions)
                    values = { 'regional_pos_title': formatted_regional_positions, }
                    StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': title}, columns=['regional_pos_title'], values=formatted_regional_positions)
                    type = 'regional'
                    value = { 'type' : type, 'title' : title, }
                    StaffingDB.delete(self=self, table='positions', where=['type', 'title'], value=value)
                    for position in new_regional_positions:
                        await StaffingDB.insert_positions(self, position, '', type, title)
                    await self._updatemessage(title)
                    await ctx.send(f'Regional Positions updated to:\n{formatted_regional_positions}\n\nThird Section Title updated to `{third_section}`')

                elif message.content == '7':
                    restrict_booking = await StaffingAsync._get_restrict_positions(self, ctx)
                    StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': title}, columns=['restrict_bookings'], values={'restrict_bookings': restrict_booking})
                    await self._updatemessage(title)
                    await ctx.send('Restrict Booking updated')

                elif message.content == '8':
                    confirm_delete = await StaffingAsync._getconfirmation(self, ctx, title)

                    if confirm_delete == title:
                        all_details = StaffingDB.select(self, table='staffing', where=['title'], value={'title': title})
                        channel_id = all_details[4]
                        message_id = all_details[5]
                        channel = self.bot.get_channel(int(channel_id))
                        message = await channel.fetch_message(int(message_id))
                        await message.delete()
                        value = { 'title' : title, }
                        StaffingDB.delete(self=self, table='staffing', where=['title'], value=value)
                        StaffingDB.delete(self=self, table='positions', where=['title'], value=value)

                        await ctx.send(f'Staffing for `{title}` has been deleted')
                    elif confirm_delete == 'CANCEL':
                        await ctx.send(f'Deletion of `{title}` has been cancelled.')

                elif message.content == '9':
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
            vatsim_member = discord.utils.get(ctx.guild.roles, id=VATSIM_MEMBER_ROLE)
            vatsca_member = discord.utils.get(ctx.guild.roles, id=VATSCA_MEMBER_ROLE)
            OBS_rating = discord.utils.get(ctx.guild.roles, id=OBS_RATING_ROLE)
            usernick = ctx.author.id
            if vatsim_member in ctx.author.roles or vatsca_member in ctx.author.roles and OBS_rating not in ctx.author.roles:
                
                event_channel = StaffingDB.select(self, table='staffing', columns=['channel_id'], amount="all")
                title = StaffingDB.select(self, table='staffing', columns=['title'], where=['channel_id'], value={'channel_id': ctx.channel.id})
                positions = StaffingDB.select(self, table='positions', columns=['position', 'user'], where=['title'], value={'title': title[0]}, amount='all')
                main_pos = StaffingDB.select(self, table="positions", columns=['position', 'user'], where=['title', 'type'], value={'title': title[0], 'type': 'main'}, amount='all')
                sec_pos = StaffingDB.select(self, table="positions", columns=['position', 'user'], where=['title', 'type'], value={'title': title[0], 'type': 'secondary'}, amount='all')
                reg_pos = StaffingDB.select(self, table="positions", columns=['position', 'user'], where=['title', 'type'], value={'title': title[0], 'type': 'regional'}, amount='all')
                eventDetails = StaffingDB.select(self, table='staffing', columns=['date', 'restrict_bookings'], where=['title'], value={'title': title[0]})

                if any(ctx.channel_id in channel for channel in event_channel):
                    if any(f'<@{usernick}>' in match for match in positions):
                        await ctx.send(f"<@{usernick}> You already have a booking!", delete_after=5)
                    elif any(position.upper() + ':' in match for match in positions):
                        if eventDetails[1] == 0:
                            await StaffingAsync._book(self, ctx, eventDetails, title, usernick, position)                            
                        else:
                            if any(position.upper() + ':' in match for match in sec_pos) and any('' in pos for pos in main_pos) or any(position.upper() + ':' in match for match in reg_pos) and any('' in pos for pos in main_pos):
                                await ctx.send(f'<@{usernick}> All main positions is required to be booked before booking any secondary positions.', delete_after=5)
                            else:
                                await StaffingAsync._book(self, ctx, eventDetails, title, usernick, position)
                    else:
                        await ctx.send(f"<@{usernick}> The bot could not find the position you tried to book.")
                else:
                    await ctx.send(f"<@{usernick}> Please use the correct channel", delete_after=5)
            else:
                await ctx.send(f"<@{usernick}> You do not have the required role to book positions", delete_after=5)

        except Exception as e:
            await ctx.send(f"Error booking position {position} - {e}")
            raise e

    @cog_ext.cog_slash(name="unbook", guild_ids=guild_id, description='Bot books selected position for selected staffing')
    async def unbook(self, ctx):
        try:
            event_channel = StaffingDB.select(self, table='staffing', columns=['channel_id'], amount='all')
            title = StaffingDB.select(self, table='staffing', columns=['title'], where=['channel_id'], value={'channel_id': ctx.channel.id})
            positions = StaffingDB.select(self, table='positions', columns=['position', 'user'], where=['title'], value={'title': title[0]}, amount='all')

            usernick = ctx.author.id
            if any(ctx.channel_id in channel for channel in event_channel):
                if any(f'<@{usernick}>' in match for match in positions):

                    cid = re.findall("\d+", str(ctx.author.nick))

                    position = StaffingDB.select(self, table='positions', columns=['position'], where=['user', 'title'], value={'user': f'<@{usernick}>', 'title': title[0]})

                    request = await Booking.delete_booking(self, int(cid[0]), str(position[0]))
                    if request == 200:
                        StaffingDB.update(self=self, table='positions', columns=['user'], values={'user': ''}, where=['user', 'title'], value={'user': f'<@{usernick}>', 'title': title[0]})
                        await self._updatemessage(title[0])
                        await ctx.send(f"<@{usernick}> Confirmed cancelling of your booking!", delete_after=5)
                    else:
                        await ctx.send(f"<@{usernick}> Cancelling failed, Control Center responded with error {request}, please try again later", delete_after=5)
            else:
                await ctx.send(f"<@{usernick}> Please use the correct channel", delete_after=5)
        except Exception as e:
            await ctx.send(f"Error unbooking position for event {title[0]} - {e}")
            raise e

    @cog_ext.cog_slash(name="refreshevent", guild_ids=guild_id, description='Bot refreshes selected event')
    async def refreshevent(self, ctx, title):
        await self._updatemessage(title)
        await ctx.send(f"{ctx.author.mention} Event `{title}` has been refreshed", delete_after=5)

    #
    # ----------------------------------
    # ASYNC DATA FUNCTIONS
    # ----------------------------------
    #
    async def _updatemessage(self, title):
        try:
            events = StaffingDB.select(self=self, table='staffing', columns=['*'], where=['title'], value={'title': title})

            title = events[1]
            date = events[2]
            description = events[3]
            channel_id = events[4]
            message_id = events[5]
            first_section = events[7]
            second_section = events[8]
            third_section = events[9]

            time = await StaffingAsync._geteventtime(self, title)
            start_time = time[0]
            end_time = time[1]

            type = 'main'
            main_pos = StaffingDB.select(self=self, table='positions', columns=['*'], where=['title', 'type'], value={'title': title, 'type': type}, amount='all')
            main_positions = []
            for position in main_pos:
                main_positions.append(f'{position[1]} {position[2]}')
                main_position_data = "\n" .join(
                    position for position in main_positions)

            type = 'secondary'
            secondary_pos = StaffingDB.select(self=self, table='positions', columns=['*'], where=['title', 'type'], value={'title': title, 'type': type}, amount='all')
            secondary_positions = []
            for position in secondary_pos:
                secondary_positions.append(f'{position[1]} {position[2]}')
                secondary_position_data = "\n" .join(
                    position for position in secondary_positions)

            type = 'regional'
            regional_pos = StaffingDB.select(self=self, table='positions', columns=['*'], where=['title', 'type'], value={'title': title, 'type': type}, amount='all')
            regional_positions = []
            for position in regional_pos:
                regional_positions.append(f'{position[1]} {position[2]}')
                regional_position_data = "\n" .join(
                    position for position in regional_positions)

            format_staffing_message = ""

            if format_staffing_message != "":
                format_staffing_message += "\n"

            formatted_date = date.strftime("%A %d/%m/%Y")
            format_staffing_message += f'{title} staffing - {formatted_date} {start_time} - {end_time}z\n\n{description}\n\n{first_section}:\n{main_position_data}\n\n{second_section}:\n{secondary_position_data}\n\n{third_section}:\n{regional_position_data}'

            channel = self.bot.get_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            await message.edit(content=format_staffing_message)

        except Exception as e:
            print(f'Unable to update message - {e}')
            raise e

    #
    # ----------------------------------
    # TASK LOOP FUNCTIONS
    # ----------------------------------
    #
    @tasks.loop(seconds=STAFFING_INTERVAL)
    async def autoreset(self):
        await self.bot.wait_until_ready()
        staffings = StaffingDB.select(self=self, table='staffing', columns=['*'], amount='all')
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
                StaffingDB.update(self=self, table='positions', columns=['user'], values={'user': ''}, where=['title'], value={'title': title})
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
                StaffingDB.update(self=self, table='staffing', columns=['date'], values={'date': newdate}, where=['title'], value={'title': title})
                await self._updatemessage(title)
                channel = self.bot.get_channel(int(staffing[4]))
                await channel.send("The chat is being automatic reset!")
                await asyncio.sleep(5)
                await channel.purge(limit=None, check=lambda msg: not msg.pinned)

def setup(bot):
    bot.add_cog(Staffingcog(bot))
