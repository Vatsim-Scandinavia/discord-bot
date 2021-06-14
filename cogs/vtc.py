import os
import fileinput
import sys
import re
from discord.ext import commands
from discord_slash import cog_ext
import datetime
from helpers.config import VTC_CHANNEL, VTC_STAFFING_MSG, GUILD_ID, VTC_POSITIONS
from helpers.message import staff_roles

guild_ids = [GUILD_ID]


class VTCcog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        """self.autoreset.start()"""

    def cog_unload(self):
        """ self.autoreset.cancel()"""

    @cog_ext.cog_slash(name="setupstaffing", guild_ids=guild_ids, description="Bot setups staffing information")
    @commands.has_any_role(*staff_roles())
    async def setupstaffing(self, ctx) -> None:
        titel = await self._get_titel(ctx)
        staffing_date = await self._get_date(ctx)
        staffing_message = await self._get_staffing_message(ctx)
        main_pos = await self._get_mainpositions_message(ctx)
        secondary_pos = await self._get_secondarypositions_message(ctx)
        regional_pos = await self._getregionalpositions_message(ctx)
        channels = await self._get_channels(ctx)

        format_staffing_message = ""

        if format_staffing_message != "":
            format_staffing_message += "\n"

        main_positions_data = "\n" .join(position for position in main_pos)
        secondary_positions_data = "\n" .join(
            position for position in secondary_pos)
        regional_positions_data = "\n" .join(
            position for position in regional_pos)

        format_staffing_message += titel + " staffing - " + staffing_date + "\n\n" + staffing_message + \
            "\n\nMain Positions:\n" + \
            str(main_positions_data) + \
            "\n\nSecondary Positions:\n" + \
            str(secondary_positions_data) + \
            "\n\nRegional Positions:\n" + str(regional_positions_data)

        for channel in channels:
            timestamp = datetime.datetime.now()
            msg = await channel.send(format_staffing_message)
            await msg.pin()
            await channel.purge(limit=None, check=lambda msg: not msg.pinned)
            with open('staffing-info/' + titel + '.txt', mode='w') as file:
                file.write("------ Created at ------\n" + str(timestamp) + "\n------------------------\n\n------ Updated at ------\n\n------------------------\n\n------ Titel ------\n" + str(titel) + "\n-------------------\n\n------ Day of event ------\n" + str(staffing_date) +
                           "\n--------------------------\n\n------ Staffing Message ------\n" + str(staffing_message) + "\n------------------------------\n\n------ Main Positions ------\n" + str(
                               main_positions_data) + "\n----------------------------\n\n------ Secondary Positions ------\n" + str(secondary_positions_data)
                           + "\n---------------------------------\n\n------ Regional Positions ------\n" + str(regional_positions_data) + "\n--------------------------------\n\n------ Channel ------\n" +
                           str(channel) + "\n---------------------\n\n------ Channel id ------\n" + str(channel.id) + "\n------------------------\n\n------ Message id ------\n" + str(msg.id) + "\n------------------------\n\n------ Original Full Staffing Message ------\n" + str(format_staffing_message) + "\n------------------------")
                print('Staffing file for ' + titel +
                      ' created at ' + str(timestamp))

    async def _get_titel(self, ctx):
        """
        Function gets a message that'll be included in announcement
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Event Title? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda
                                              message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            if os.path.isfile('staffing-info/' + message.content + '.txt'):
                await ctx.send('Setup cancelled. A staffing with that name already exists.')
                raise ValueError

            return message.content
        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    async def _get_date(self, ctx):
        """
        Function gets a message that'll be included in announcement
        :param ctx:
        :return:
        """
        try:
            available_days = ['Monday', 'Tuesday', 'Wednesday',
                              'Thursday', 'Friday', 'Saturday', 'Sunday']

            await ctx.send('Event Day of the week? **FYI this command expires in 1 minute** Available days: ' + str(available_days)[1:-1])
            message = await self.bot.wait_for('message', timeout=60, check=lambda
                                              message: message.author == ctx.author and ctx.channel == message.channel)

            if message.content == available_days[0]:
                today = datetime.date.today()
                next_monday = today + \
                    datetime.timedelta(days=0-today.weekday(), weeks=1)
                date_formatted = next_monday.strftime("%A %d/%m/%Y")
                return date_formatted

            elif message.content == available_days[1]:
                today = datetime.date.today()
                next_tuesday = today + \
                    datetime.timedelta(days=1-today.weekday(), weeks=1)
                date_formatted = next_tuesday.strftime("%A %d/%m/%Y")
                return date_formatted

            elif message.content == available_days[2]:
                today = datetime.date.today()
                next_wednesday = today + \
                    datetime.timedelta(days=2-today.weekday(), weeks=1)
                date_formatted = next_wednesday.strftime("%A %d/%m/%Y")
                return date_formatted

            elif message.content == available_days[3]:
                today = datetime.date.today()
                next_thursday = today + \
                    datetime.timedelta(days=3-today.weekday(), weeks=1)
                date_formatted = next_thursday.strftime("%A %d/%m/%Y")
                return date_formatted

            elif message.content == available_days[4]:
                today = datetime.date.today()
                next_friday = today + \
                    datetime.timedelta(days=4-today.weekday(), weeks=1)
                date_formatted = next_friday.strftime("%A %d/%m/%Y")
                return date_formatted

            elif message.content == available_days[5]:
                today = datetime.date.today()
                next_saturday = today + \
                    datetime.timedelta(days=5-today.weekday(), weeks=1)
                date_formatted = next_saturday.strftime("%A %d/%m/%Y")
                return date_formatted

            elif message.content == available_days[6]:
                today = datetime.date.today()
                next_sunday = today + \
                    datetime.timedelta(days=6-today.weekday(), weeks=1)
                date_formatted = next_sunday.strftime("%A %d/%m/%Y")
                return date_formatted

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    async def _get_staffing_message(self, ctx):
        """
        Function gets a message that'll be included in announcement
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Staffing message? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda
                                              message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    async def _get_mainpositions_message(self, ctx):
        """
        Function gets a message that'll be included in announcement
        :param ctx:
        :return:
        """
        try:

            position = []
            types = 'Main'
            times = await self._get_howmanypositions_message(ctx, types)
            num = 0
            for _ in range(int(times)):
                num += 1
                await ctx.send('Main position nr. ' + str(num) + '? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda
                                                  message: message.author == ctx.author and ctx.channel == message.channel)
                position.append(message.content + ":")

                if len(message.content) < 1:
                    await ctx.send('Setup cancelled. No positions was provided.')
                    raise ValueError

            return position
        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    async def _get_secondarypositions_message(self, ctx):
        """
        Function gets a message that'll be included in announcement
        :param ctx:
        :return:
        """
        try:

            position = []
            types = 'Secondary'
            times = await self._get_howmanypositions_message(ctx, types)
            num = 0
            for _ in range(int(times)):
                num += 1
                await ctx.send('Secondary position nr. ' + str(num) + '? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda
                                                  message: message.author == ctx.author and ctx.channel == message.channel)
                position.append(message.content + ":")

                if len(message.content) < 1:
                    await ctx.send('Setup cancelled. No positions was provided.')
                    raise ValueError

            return position
        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    async def _getregionalpositions_message(self, ctx):
        """
        Function gets a message that'll be included in announcement
        :param ctx:
        :return:
        """
        try:

            position = []
            types = 'Regional'
            times = await self._get_howmanypositions_message(ctx, types)
            num = 0
            for _ in range(int(times)):
                num += 1
                await ctx.send('Regional position nr. ' + str(num) + '? **FYI this command expires in 1 minute**')
                message = await self.bot.wait_for('message', timeout=60, check=lambda
                                                  message: message.author == ctx.author and ctx.channel == message.channel)
                position.append(message.content + ":")

                if len(message.content) < 1:
                    await ctx.send('Setup cancelled. No positions was provided.')
                    raise ValueError

            return position
        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    async def _get_howmanypositions_message(self, ctx, types):
        """
        Function gets a message that'll be included in announcement
        :param ctx:
        :return:
        """
        try:
            await ctx.send('How many ' + types + ' positions? **FYI this command expires in 1 minute**')
            message = await self.bot.wait_for('message', timeout=60, check=lambda
                                              message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    async def _get_channels(self, ctx):
        """
        Function gets channels where it should send the announcement
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Where would you like to post the staffing message? **FYI this command expires in 1 minute**')

            message = await self.bot.wait_for('message', timeout=60, check=lambda
                                              message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.channel_mentions) < 1:
                await ctx.send('Setup canceled. No channel provided.')
                raise ValueError

            return message.channel_mentions
        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    @cog_ext.cog_slash(name="showallstaffings", guild_ids=guild_ids, description="Bot shows all staffings available")
    @commands.has_any_role(*staff_roles())
    async def showallstaffings(self, ctx) -> None:
        showall = os.listdir("staffing-info")
        allstaffings = []
        for x in showall:
            allstaffings.append(os.path.splitext(x)[0])
        show_all_staffings = "\n" .join(files for files in allstaffings)
        await ctx.send("All Staffings:\n**`" + str(show_all_staffings) + "`**")

    @cog_ext.cog_slash(name="updatestaffing", guild_ids=guild_ids, description="Bot updates selected staffing")
    @commands.has_any_role(*staff_roles())
    async def updatestaffing(self, ctx, titel) -> None:
        try:
            showall = os.listdir("staffing-info")

            if titel + ".txt" in showall:
                options = ['Titel', 'Day of event', 'Staffing message',
                           'Main Positions', 'Secondary Positions', 'Regional Positions', 'Exit Updater']
                avail = "\n" .join(files for files in options)
                await ctx.send('What would you like to update? **FYI this command expires in 1 minute**\n\nAvailable options:\n' + str(avail))

                message = await self.bot.wait_for('message', timeout=60, check=lambda
                                                  message: message.author == ctx.author and ctx.channel == message.channel)

                if message.content == options[0]:
                    newtitel = await self._update_titel(ctx)
                    headings = []
                    start = 0
                    with open('staffing-info/' + titel + ".txt") as f:
                        for ln in f:
                            # append to heading list
                            if start == 1:
                                # when the second dashed line is seen, stop appending
                                if ln.startswith('---'):
                                    start = 0
                                    continue
                                headings.append(ln.rstrip())
                            # first dashed line, indicate to start appending
                            if ln.startswith('------ Titel ------'):
                                start = 1
                    if headings[0] == titel:
                        for line in fileinput.input(['staffing-info/' + titel + '.txt'], inplace=True):
                            if line.startswith(titel):
                                line = newtitel + '\n'
                            sys.stdout.write(line)
                        os.rename('staffing-info/' + titel + '.txt',
                                  'staffing-info/' + newtitel + '.txt')
                        await ctx.send("Titel Updated to - '" + newtitel + "'")
                        await self._update_message(ctx, titel)
                    else:
                        await ctx.send('Titels does not match.')

                if message.content == options[1]:
                    newdate = await self._get_date(ctx)
                    headings = []
                    start = 0
                    with open('staffing-info/' + titel + ".txt") as f:
                        for ln in f:
                            # append to heading list
                            if start == 1:
                                # when the second dashed line is seen, stop appending
                                if ln.startswith('---'):
                                    start = 0
                                    continue
                                headings.append(ln.rstrip())
                            if ln.startswith('------ Day of event ------'):
                                start = 1
                    for line in fileinput.input(['staffing-info/' + titel + '.txt'], inplace=True):
                        if line.startswith(headings[0]):
                            line = newdate + '\n'
                        sys.stdout.write(line)
                    await ctx.send("Day of event Updated to - '" + newdate + "'")
                    await self._update_message(ctx, titel)

                if message.content == options[2]:
                    new_staffing_msg = await self._get_staffing_message(ctx)

                    headings = []
                    start = 0
                    with open('staffing-info/' + titel + ".txt") as f:
                        for ln in f:
                            # append to heading list
                            if start == 1:
                                # when the second dashed line is seen, stop appending
                                if ln.startswith('---'):
                                    start = 0
                                    continue
                                headings.append(ln.rstrip())
                            if ln.startswith('------ Staffing Message ------'):
                                start = 1
                    state = 0
                    for line in fileinput.input('staffing-info/' + titel + '.txt', inplace=True):
                        if state == 1:
                            if line.startswith('---'):
                                state = 0
                                line.replace(str(headings), "")
                                continue
                        if line.startswith('------ Staffing Message ------'):
                            state = 1
                        sys.stdout.write(line)
                        
                    await self._update_message(ctx, titel)
                    await ctx.send("Staffing message Updated to - '" + new_staffing_msg + "'")

                if message.content == options[3]:
                    new_main_pos = await self._get_mainpositions_message(ctx)
                    headings = []
                    start = 0
                    with open('staffing-info/' + titel + ".txt") as f:
                        for ln in f:
                            # append to heading list
                            if start == 1:
                                # when the second dashed line is seen, stop appending
                                if ln.startswith('---'):
                                    start = 0
                                    continue
                                headings.append(ln.rstrip())
                            # first dashed line, indicate to start appending
                            if ln.startswith('------ Main Positions ------'):
                                start = 1
                    for line in fileinput.input(['staffing-info/' + titel + '.txt'], inplace=True):
                        if line.startswith(headings[0]):
                            main_positions_data = "\n" .join(position for position in new_main_pos)
                            line = str(main_positions_data) + '\n'
                        sys.stdout.write(line)
                    await ctx.send("Main positions Updated to - '" + str(new_main_pos) + "'")
                    await self._update_message(ctx, titel)

                if message.content == options[4]:
                    new_secondary_pos = await self._get_secondarypositions_message(ctx)
                    headings = []
                    start = 0
                    with open('staffing-info/' + titel + ".txt") as f:
                        for ln in f:
                            # append to heading list
                            if start == 1:
                                # when the second dashed line is seen, stop appending
                                if ln.startswith('---'):
                                    start = 0
                                    continue
                                headings.append(ln.rstrip())
                            # first dashed line, indicate to start appending
                            if ln.startswith('------ Secondary Positions ------'):
                                start = 1
                    for line in fileinput.input(['staffing-info/' + titel + '.txt'], inplace=True):
                        if line.startswith(headings[0]):
                            secondary_positions_data = "\n" .join(position for position in new_secondary_pos)
                            line = str(secondary_positions_data) + '\n'
                        sys.stdout.write(line)
                    await ctx.send("Secondary positions Updated to - '" + str(new_secondary_pos) + "'")
                    await self._update_message(ctx, titel)

                if message.content == options[5]:
                    new_regonal_pos = await self._getregionalpositions_message(ctx)
                    headings = []
                    start = 0
                    with open('staffing-info/' + titel + ".txt") as f:
                        for ln in f:
                            # append to heading list
                            if start == 1:
                                # when the second dashed line is seen, stop appending
                                if ln.startswith('---'):
                                    start = 0
                                    continue
                                headings.append(ln.rstrip())
                            # first dashed line, indicate to start appending
                            if ln.startswith('------ Regional Positions ------'):
                                start = 1
                    for line in fileinput.input(['staffing-info/' + titel + '.txt'], inplace=True):
                        if line.startswith(headings[0]):
                            regional_positions_data = "\n" .join(position for position in new_regonal_pos)
                            line = str(regional_positions_data) + '\n'
                        sys.stdout.write(line)
                    await ctx.send("Regional positions Updated to - '" + str(new_regonal_pos) + "'")
                    await self._update_message(ctx, titel)

                if len(message.content) < 1:
                    await ctx.send('Update canceled. No option provided.')
                    raise ValueError
            else:
                await ctx.send("Staffing not found.")

        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    async def _update_titel(self, ctx):
        try:
            await ctx.send('What should the new titel be? **FYI this command expires in 1 minute**')

            message = await self.bot.wait_for('message', timeout=60, check=lambda
                                              message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Update canceled. No titel provided.')
                raise ValueError

            return message.content
        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    async def _update_message(self, ctx, titel):
        try:
            channel_id = await self._get_channel_id(titel)
            message_id = await self._get_message_id(titel)
            staffing_date = await self._get_staffing_date(titel)
            staffing_message = await self._get_staffing_msg(titel)
            main_position = await self._get_all_main_pos(titel)
            secondary_position = await self._get_all_secondary_pos(titel)
            regional_position = await self._get_all_regional_pos(titel)

            format_staffing_message = ""

            if format_staffing_message != "":
                format_staffing_message += "\n"

            staffing_msg_formatted = "\n" .join(msg for msg in staffing_message)
            main_positions_data = "\n" .join(position for position in main_position)
            secondary_positions_data = "\n" .join(
            position for position in secondary_position)
            regional_positions_data = "\n" .join(
            position for position in regional_position)

            format_staffing_message += titel + " staffing - " + staffing_date[0] + "\n\n" + str(staffing_msg_formatted) + \
                "\n\nMain Positions:\n" + \
                str(main_positions_data) + \
                "\n\nSecondary Positions:\n" + \
                str(secondary_positions_data) + \
                "\n\nRegional Positions:\n" + str(regional_positions_data)

            channel = self.bot.get_channel(int(channel_id[0]))
            message = await channel.fetch_message(int(message_id[0]))
            await message.edit(content=format_staffing_message)
        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    async def _get_channel_id(self, titel):
        channel_id = []
        start = 0
        with open('staffing-info/' + titel + ".txt") as f:
            for ln in f:
                # append to heading list
                if start == 1:
                    # when the second dashed line is seen, stop appending
                    if ln.startswith('---'):
                        start = 0
                        continue
                    channel_id.append(ln.rstrip())
                    # first dashed line, indicate to start appending
                if ln.startswith('------ Channel id ------'):
                    start = 1
        return channel_id

    async def _get_message_id(self, titel):
        message_id = []
        start = 0
        with open('staffing-info/' + titel + ".txt") as f:
            for ln in f:
                # append to heading list
                if start == 1:
                    # when the second dashed line is seen, stop appending
                    if ln.startswith('---'):
                        start = 0
                        continue
                    message_id.append(ln.rstrip())
                    # first dashed line, indicate to start appending
                if ln.startswith('------ Message id ------'):
                    start = 1
        return message_id

    async def _get_staffing_date(self, titel):
        staffing_date = []
        start = 0
        with open('staffing-info/' + titel + ".txt") as f:
            for ln in f:
                # append to heading list
                if start == 1:
                    # when the second dashed line is seen, stop appending
                    if ln.startswith('---'):
                        start = 0
                        continue
                    staffing_date.append(ln.rstrip())
                    # first dashed line, indicate to start appending
                if ln.startswith('------ Day of event ------'):
                    start = 1
        return staffing_date

    async def _get_staffing_msg(self, titel):
        staffing_msg = []
        start = 0
        with open('staffing-info/' + titel + ".txt") as f:
            for ln in f:
                # append to heading list
                if start == 1:
                    # when the second dashed line is seen, stop appending
                    if ln.startswith('---'):
                        start = 0
                        continue
                    staffing_msg.append(ln.rstrip())
                    # first dashed line, indicate to start appending
                if ln.startswith('------ Staffing Message ------'):
                    start = 1
        return staffing_msg

    async def _get_all_main_pos(self, titel):
        main_pos = []
        start = 0
        with open('staffing-info/' + titel + ".txt") as f:
            for ln in f:
                # append to heading list
                if start == 1:
                    # when the second dashed line is seen, stop appending
                    if ln.startswith('---'):
                        start = 0
                        continue
                    main_pos.append(ln.rstrip())
                    # first dashed line, indicate to start appending
                if ln.startswith('------ Main Positions ------'):
                    start = 1
        return main_pos

    async def _get_all_secondary_pos(self, titel):
        secondary_pos = []
        start = 0
        with open('staffing-info/' + titel + ".txt") as f:
            for ln in f:
                # append to heading list
                if start == 1:
                    # when the second dashed line is seen, stop appending
                    if ln.startswith('---'):
                        start = 0
                        continue
                    secondary_pos.append(ln.rstrip())
                    # first dashed line, indicate to start appending
                if ln.startswith('------ Secondary Positions ------'):
                    start = 1
        return secondary_pos

    async def _get_all_regional_pos(self, titel):
        regional_pos = []
        start = 0
        with open('staffing-info/' + titel + ".txt") as f:
            for ln in f:
                # append to heading list
                if start == 1:
                    # when the second dashed line is seen, stop appending
                    if ln.startswith('---'):
                        start = 0
                        continue
                    regional_pos.append(ln.rstrip())
                    # first dashed line, indicate to start appending
                if ln.startswith('------ Regional Positions ------'):
                    start = 1
        return regional_pos

    @cog_ext.cog_slash(name="book", guild_ids=guild_ids, description="Bot updates selected staffing")
    async def book(self, ctx, titel, position: str) -> None:
        try:
            main_pos = await self._get_all_main_pos(titel)
            secondary_pos = await self._get_all_secondary_pos(titel)
            regional_pos = await self._get_all_regional_pos(titel)
            positions = []
            positions.extend(main_pos + secondary_pos + regional_pos)

            usernick = ctx.author.id
            if position + ":" in positions:
                if str(usernick) in positions:
                    await ctx.send("<@" + str(usernick) + "> You already have a booking.")
                elif str(usernick) not in positions:
                    for line in fileinput.input(['staffing-info/' + titel + '.txt'], inplace=True):
                        if str(usernick) not in line and line.startswith(position + ":"):
                            line = position + ': <@' + str(usernick) + '>\n'
                        sys.stdout.write(line)
                await ctx.send("<@" + str(usernick) + "> Confirmed booking for " + position + "!")
                await self._update_message(ctx, titel)
            else:
                await ctx.send("<@" + str(usernick) + "> The position " + position + " does not exist or is already booked.")

        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    @cog_ext.cog_slash(name="unbook", guild_ids=guild_ids, description="Bot updates selected staffing")
    async def unbook(self, ctx, titel, position: str) -> None:
        try:
            usernick = ctx.author.id
            main_pos = await self._get_all_main_pos(titel)
            secondary_pos = await self._get_all_secondary_pos(titel)
            regional_pos = await self._get_all_regional_pos(titel)
            positions = []
            positions.extend(main_pos + secondary_pos + regional_pos)
            for line in fileinput.input(['staffing-info/' + titel + '.txt'], inplace=True):
                if line.startswith(position) and str(usernick) in line:
                    line = position + ':\n'
                sys.stdout.write(line)
            await ctx.send("<@" + str(usernick) + "> Confirmed unbooking for " + position + "!")
            await self._update_message(ctx, titel)

        except Exception as exception:
            await ctx.send(str(exception))
            raise exception

    @cog_ext.cog_slash(name="update_staffing_message", guild_ids=guild_ids, description="Bot updates staffing message ***TESTING ONLY***")
    @commands.has_any_role(*staff_roles())
    async def update_staffing_message(self, ctx) -> None:
        channel_id = 849206253330497537
        message_id = 850509348597792779
        channel = self.bot.get_channel(int(channel_id))
        message = await channel.fetch_message(message_id)
        await message.edit(content="test")
        await ctx.send("Updating Message")


def setup(bot):
    bot.add_cog(VTCcog(bot))
