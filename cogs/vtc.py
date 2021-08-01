import datetime
import asyncio

from discord.ext import commands, tasks
from discord.ext.commands import cog
from discord.ext.commands.core import check
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_choice, create_option

from helpers.config import GUILD_ID, AVAILABLE_EVENT_DAYS
from helpers.message import staff_roles
from helpers.database import db_connection

guild_id = [GUILD_ID]

class VTCcog(commands.Cog):
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
    async def setupstaffing(self, ctx) -> None:
        title = await self._get_title(ctx)
        date = await self._get_date(ctx)
        description = await self._get_description(ctx)
        main_position = await self._get_main_positions(ctx)
        secondary_position = await self._get_secondary_positions(ctx)
        regional_position = await self._get_regional_positions(ctx)
        channels = await self._get_channel(ctx)

        format_staffing_message = ""

        if format_staffing_message != "":
            format_staffing_message += "\n"

        main_position_data = "\n" .join(position for position in main_position)
        secondary_position_data = "\n" .join(position for position in secondary_position)
        regional_position_data = "\n" .join(position for position in regional_position)

        formatted_date = date.strftime("%A %d/%m/%Y")

        format_staffing_message += f'{title} staffing - {formatted_date}\n\n{description}\n\nMain Positions:\n{main_position_data}\n\nSecondary Positions:\n{secondary_position_data}\n\nRegional Positions:\n{regional_position_data}'

        mydb = db_connection()
        cursor = mydb.cursor()

        for channel in channels:
            msg = await channel.send(format_staffing_message)
            await msg.pin()
            await channel.purge(limit=None, check=lambda msg: not msg.pinned)
            cursor.execute(
                'INSERT INTO staffing(title, date, description, channel_id, message_id) VALUES (%s, %s, %s, %s, %s)', 
                (
                    title,
                    date,
                    description,
                    channel.id,
                    msg.id
                )
            )

            mydb.commit()

            type = 'main'
            for position in main_position:
                cursor.execute(
                    'INSERT INTO positions(position, user, type, title) VALUES (%s, "", %s, %s)',
                    (
                        position,
                        type,
                        title
                    )
                )
                mydb.commit()

            type = 'secondary'
            for position in secondary_position:
                cursor.execute(
                    'INSERT INTO positions(position, user, type, title) VALUES (%s, "", %s, %s)',
                    (
                        position,
                        type,
                        title
                    )
                )
                mydb.commit()

            type = 'regional'
            for position in regional_position:
                cursor.execute(
                    'INSERT INTO positions(position, user, type, title) VALUES (%s, "", %s, %s)',
                    (
                        position,
                        type,
                        title
                    )
                )
                mydb.commit()

    @cog_ext.cog_slash(name="showallstaffings", guild_ids=guild_id, description="Bot shows all staffings available")
    @commands.has_any_role(*staff_roles())
    async def showallstaffings(self, ctx) -> None:
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

    @cog_ext.cog_slash(name="updatestaffing", guild_ids=guild_id, description='Bot updates selected staffing', options=[
        create_option(
            name='title',
            description='Select which event you want to update',
            option_type=3,
            required=True,
            choices=[
                create_choice(
                    name='Vectors to Copenhagen',
                    value='Vectors to Copenhagen'
                ),
                create_choice(
                    name='VTC',
                    value='VTC'
                )
            ]
        )
    ])
    @commands.has_any_role(*staff_roles())
    async def updatestaffing(self, ctx, title) -> None:
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
                options = ['Title', 'Day of event', 'Staffing message', 'Main Positions', 'Secondary Positions', 'Regional Positions', 'Delete Staffing', 'Exit Updater']
                avail = "\n" .join(files for files in options)
                await ctx.send(f'What would you like to update in staffing `{title}`? **FYI this command expires in 1 minute**\n\nAvailable options:\n{avail}')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

                if message.content == options[0]:
                    newtitle = await self._get_title(ctx)
                    cursor.execute(
                        'UPDATE staffing, positions SET staffing.title = %s, positions.title = %s WHERE staffing.title = %s and positions.title = %s',
                        (
                            newtitle,
                            newtitle,
                            title,
                            title
                        )
                    )
                    mydb.commit()
                    title = newtitle
                    await self._updatemessage(title)
                    await ctx.send(f'Title updated to - {newtitle}')

                elif message.content == options[1]:
                    newdate = await self._get_date(ctx)
                    cursor.execute(
                        'UPDATE staffing SET date = %s WHERE title = %s',
                        (
                            newdate,
                            title
                        )
                    )
                    mydb.commit()
                    await self._updatemessage(title)
                    formatted_date = newdate.strftime("%A %d/%m/%Y")
                    await ctx.send(f'Event date has been updated to - {formatted_date}')
                
                elif message.content == options[2]:
                    newdescription = await self._get_description(ctx)
                    cursor.execute(
                        'UPDATE staffing SET description = %s WHERE title = %s',
                        (
                            newdescription,
                            title
                        )
                    )
                    mydb.commit()
                    await self._updatemessage(title)
                    await ctx.send(f'Event description/staffing message has been updated to:\n{newdescription}')

                elif message.content == options[3]:
                    new_main_positions = await self._get_main_positions(ctx)
                    formatted_main_positions = "\n" .join(position for position in new_main_positions)
                    type = 'main'
                    cursor.execute(f"DELETE FROM positions WHERE type = '{type}' and title = '{title}'")
                    for position in new_main_positions:
                        cursor.execute('INSERT INTO positions(position, user, type, title) VALUES (%s, "", %s, %s)',
                        (
                            position,
                            type,
                            title
                        ))
                    mydb.commit()
                    await self._updatemessage(title)
                    await ctx.send(f'Main Positions updated to:\n{formatted_main_positions}')

                elif message.content == options[4]:
                    new_secondary_positions = await self._get_secondary_positions(ctx)
                    formatted_secondary_positions = "\n" .join(position for position in new_secondary_positions)
                    type = 'secondary'
                    cursor.execute(f"DELETE FROM positions WHERE type = '{type}' and title = '{title}'")
                    for position in new_secondary_positions:
                        cursor.execute('INSERT INTO positions(position, user, type, title) VALUES (%s, "", %s, %s)',
                        (
                            position,
                            type,
                            title
                        ))
                    mydb.commit()
                    await self._updatemessage(title)
                    await ctx.send(f'Secondary Positions updated to:\n{formatted_secondary_positions}')

                elif message.content == options[5]:
                    new_regional_positions = await self._get_regional_positions(ctx)
                    formatted_regional_positions = "\n" .join(position for position in new_regional_positions)
                    type = 'regional'
                    cursor.execute(f"DELETE FROM positions WHERE type = '{type}' and title = '{title}'")
                    for position in new_regional_positions:
                        cursor.execute('INSERT INTO positions(position, user, type, title) VALUES (%s, "", %s, %s)',
                        (
                            position,
                            type,
                            title
                        ))
                    mydb.commit()
                    await self._updatemessage(title)
                    await ctx.send(f'Regional Positions updated to:\n{formatted_regional_positions}')

                elif message.content == options[6]:
                    confirm_delete = await self._getconfirmation(ctx, title)

                    if confirm_delete == title:
                        cursor.execute(f"SELECT * FROM staffing WHERE title = '{title}'")
                        all_details = cursor.fetchone()
                        channel_id = all_details[4]
                        message_id = all_details[5]
                        channel = self.bot.get_channel(int(channel_id))
                        message = await channel.fetch_message(int(message_id))
                        await message.delete()
                        cursor.execute(f"DELETE FROM staffing WHERE title = '{title}'")
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
    async def book(self, ctx, title, position) -> None:
        try:
            mydb = db_connection()
            cursor = mydb.cursor()
            cursor.execute(f"SELECT position, user FROM positions WHERE title ='{title}'")

            positions = cursor.fetchall()

            cursor.execute(f"SELECT channel_id FROM staffing WHERE title = '{title}'")
            
            event_data = cursor.fetchone()
            usernick = ctx.author.id
            if ctx.channel.id == event_data[0]:
                mydb.reconnect()
                if any(f'<@{usernick}>' in match for match in positions):
                    await ctx.send(f"<@{usernick}> You already have a booking!")
                    await asyncio.sleep(5)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                elif any(position + ':' in match for match in positions):
                    cursor.execute(f"UPDATE positions SET user = '<@{usernick}>' WHERE position = '{position}:' and title = '{title}'")
                    mydb.commit()
                    await self._updatemessage(title)
                    await ctx.send(f"<@{usernick}> Confirmed booking for position {position} for event {title}")
                    await asyncio.sleep(5)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
            else:
                await ctx.send(f"<@{usernick}> Please use the <#{event_data[0]}> channel")
                await asyncio.sleep(5)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        except Exception as e:
            await ctx.send(f"Error booking position {position} for event {title} - {e}")
            raise e

    @cog_ext.cog_slash(name="unbook", guild_ids=guild_id, description='Bot books selected position for selected staffing')
    async def unbook(self, ctx, title) -> None:
        try:
            mydb = db_connection()
            cursor = mydb.cursor()

            cursor.execute(f"SELECT position, user FROM positions WHERE title = '{title}'")
            
            positions = cursor.fetchall()

            cursor.execute(f"SELECT channel_id FROM staffing WHERE title = '{title}'")

            event_data = cursor.fetchone()

            usernick = ctx.author.id
            if ctx.channel.id == event_data[0]:
                mydb.reconnect()
                if any(f'<@{usernick}>' in match for match in positions):
                    cursor.execute(f"UPDATE positions SET user = '' WHERE user = '<@{usernick}>' and title = '{title}'")
                    mydb.commit()
                    await self._updatemessage(title)
                    await ctx.send(f"<@{usernick}> Confirmed cancelling of your booking!")
                    await asyncio.sleep(5)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
            else:
                await ctx.send(f"<@{usernick}> Please use the <#{event_data[0]}> channel")
                await asyncio.sleep(5)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        except Exception as e:
            await ctx.send(f"Error unbooking position for event {title} - {e}")
            raise e

    #
    # ----------------------------------
    # TASK LOOP FUNCTIONS
    # ----------------------------------
    #

    @tasks.loop(seconds=60)
    async def autoreset(self) -> None:
        await self.bot.wait_until_ready()
        mydb = db_connection()
        cursor = mydb.cursor()
        cursor.execute('SELECT * FROM staffing')
        staffings = cursor.fetchall()
        now = datetime.datetime.today()

        for staffing in staffings:
            date = staffing[2]
            day = date.strftime("%d")
            month = date.strftime("%m")
            year = date.strftime("%Y")
            formatted_date = datetime.datetime(int(year), int(month), int(day))
            if now.date() == formatted_date.date() and now.hour == 1 and 15 <= now.minute <= 15:
                title = staffing[1]
                cursor.execute(f"UPDATE positions SET user = '' WHERE title = '{title}'")
                newdate = ''
                if formatted_date.weekday() == 0:
                    today = datetime.date.today()
                    newdate = today + datetime.timedelta(days=0-today.weekday(), weeks=1)

                elif formatted_date.weekday() == 1:
                    today = datetime.date.today()
                    newdate = today + datetime.timedelta(days=1-today.weekday(), weeks=1)

                elif formatted_date.weekday() == 2:
                    today = datetime.date.today()
                    newdate = today + datetime.timedelta(days=2-today.weekday(), weeks=1)

                elif formatted_date.weekday() == 3:
                    today = datetime.date.today()
                    newdate = today + datetime.timedelta(days=3-today.weekday(), weeks=1)

                elif formatted_date.weekday() == 4:
                    today = datetime.date.today()
                    newdate = today + datetime.timedelta(days=4-today.weekday(), weeks=1)

                elif formatted_date.weekday() == 5:
                    today = datetime.date.today()
                    newdate = today + datetime.timedelta(days=5-today.weekday(), weeks=1)

                elif formatted_date.weekday() == 6:
                    today = datetime.date.today()
                    newdate = today + datetime.timedelta(days=6-today.weekday(), weeks=1)
                
                cursor.execute(f"UPDATE staffing SET date = '{newdate}' WHERE title = '{title}'")
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

    async def _get_date(self, ctx):
        """
        Function gets the date of the event from a message that'll be included in the staffing message
        :param ctx:
        :return:
        """
        try:
            avail_days = AVAILABLE_EVENT_DAYS

            await ctx.send('Event Day of the week? **FYI this command expires in 1 minute** Available days: ' + str(avail_days)[1:-1])
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if message.content == avail_days[0]:
                today = datetime.date.today()
                event_day = today + datetime.timedelta(days=0-today.weekday(), weeks=1)

            elif message.content == avail_days[1]:
                today = datetime.date.today()
                event_day = today + datetime.timedelta(days=1-today.weekday(), weeks=1)

            elif message.content == avail_days[2]:
                today = datetime.date.today()
                event_day = today + datetime.timedelta(days=2-today.weekday(), weeks=1)

            elif message.content == avail_days[3]:
                today = datetime.date.today()
                event_day = today + datetime.timedelta(days=3-today.weekday(), weeks=1)

            elif message.content == avail_days[4]:
                today = datetime.date.today()
                event_day = today + datetime.timedelta(days=4-today.weekday(), weeks=1)

            elif message.content == avail_days[5]:
                today = datetime.date.today()
                event_day = today + datetime.timedelta(days=5-today.weekday(), weeks=1)

            elif message.content == avail_days[6]:
                today = datetime.date.today()
                event_day = today + datetime.timedelta(days=6-today.weekday(), weeks=1)

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
            await ctx.send('Staffing message? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as e:
            await ctx.send(f'Error getting the Staffing message - {e}')
            raise e
        
    async def _get_main_positions(self, ctx):
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
                await ctx.send(f'Main position nr. {num}? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)
                position.append(message.content + ':')

            if len(message.content) < 1:
                    await ctx.send('Setup cancelled. No positions was provided.')
                    raise ValueError

            return position
        except Exception as e:
            await ctx.send(f'Error getting main positions - {e}')
            raise e

    async def _get_secondary_positions(self, ctx):
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
                await ctx.send(f'Secondary position nr. {num}? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)
                position.append(message.content + ':')

            if len(message.content) < 1:
                    await ctx.send('Setup cancelled. No positions was provided.')
                    raise ValueError

            return position
        except Exception as e:
            await ctx.send(f'Error getting secondary positions - {e}')
            raise e

    async def _get_regional_positions(self, ctx):
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
                await ctx.send(f'Regional position nr. {num}? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)
                position.append(message.content + ':')

            if len(message.content) < 1:
                    await ctx.send('Setup cancelled. No positions was provided.')
                    raise ValueError

            return position
        except Exception as e:
            await ctx.send(f'Error getting regional positions - {e}')
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

    async def _read_titles(self):
        try:
            mydb = db_connection()
            cursor = mydb.cursor()

            cursor.execute(
                'SELECT title FROM STAFFING'
            )
            titles = cursor.fetchall()
            all_titles = []
            for title in titles:
                all_titles.append(title[0])
            return all_titles
        except Exception as e:
            await print(f'Error reading titles - {e}')
            raise e

    async def _updatemessage(self, title):
        try:
            mydb = db_connection()
            cursor = mydb.cursor()
            cursor.execute(f"SELECT * FROM staffing WHERE title = '{title}'")

            events = cursor.fetchone()

            title = events[1]
            date = events[2]
            description = events[3]
            channel_id = events[4]
            message_id = events[5]

            type = 'main'
            cursor.execute(f"SELECT * FROM positions WHERE title = '{title}' and type = '{type}'")
            main_pos = cursor.fetchall()
            main_positions = []
            for position in main_pos:
                main_positions.append(f'{position[1]} {position[2]}')
                main_position_data = "\n" .join(position for position in main_positions)

            type = 'secondary'
            cursor.execute(f"SELECT * FROM positions WHERE title = '{title}' and type = '{type}'")
            secondary_pos = cursor.fetchall()
            secondary_positions = []
            for position in secondary_pos:
                secondary_positions.append(f'{position[1]} {position[2]}')
                secondary_position_data = "\n" .join(position for position in secondary_positions)

            type = 'regional'
            cursor.execute(f"SELECT * FROM positions WHERE title = '{title}' and type = '{type}'")
            regional_pos = cursor.fetchall()
            regional_positions = []
            for position in regional_pos:
                regional_positions.append(f'{position[1]} {position[2]}')
                regional_position_data = "\n" .join(position for position in regional_positions)

            format_staffing_message = ""

            if format_staffing_message != "":
                format_staffing_message += "\n"

            mydb.reconnect()

            formatted_date = date.strftime("%A %d/%m/%Y")
            format_staffing_message += f'{title} staffing - {formatted_date}\n\n{description}\n\nMain Positions:\n{main_position_data}\n\nSecondary Positions:\n{secondary_position_data}\n\nRegional Positions:\n{regional_position_data}'

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
    bot.add_cog(VTCcog(bot))