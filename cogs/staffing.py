from typing_extensions import Literal
import discord
import asyncio
import re

from discord import app_commands, TextChannel, SelectOption
from discord.ext import commands, tasks
from discord.ui import Select, View

from datetime import datetime

from helpers.booking import Booking
from helpers.message import staff_roles, controller_roles
from helpers.staffing_async import StaffingAsync
from helpers.staffing_db import StaffingDB
from helpers.select import SelectView
from helpers.config import STAFFING_INTERVAL, DEBUG, VATSIM_MEMBER_ROLE, VATSCA_MEMBER_ROLE

class StaffingCog(commands.Cog):
    #
    # ----------------------------------
    # COG FUNCTIONS
    # ----------------------------------
    #
    def __init__(self, bot) -> None:
        self.bot = bot
        self.autoreset.start()

    def cog_unload(self):
        self.autoreset.cancel()


    #
    # ----------------------------------
    # SLASH COMMAND FUNCTIONS
    # ----------------------------------
    #
    @app_commands.command(name="setupstaffing", description="Bot setups staffing information")
    @app_commands.describe(title="What should the title of the staffing be?", week_int="What should the week interval be? eg. 1 then the date will be selected each week.", section_amount="What should the section amount be? eg. 3 then there will be 3 sections.", restrict_booking="Should the staffing restrict booking to first section before allowing other sections too?")
    @app_commands.checks.has_any_role(*staff_roles())
    async def setup_staffing(self, interaction: discord.Integration, title: StaffingAsync._get_titles(), week_int: app_commands.Range[int, 1, 4], section_amount: app_commands.Range[int, 1, 3], restrict_booking: Literal["Yes", "No"], channel: TextChannel):
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx
        dates = await StaffingAsync._geteventdate(self, title)
        description = await StaffingAsync._get_description(self, ctx)
        description = description + "\n\nTo book a position, write `/book`, press TAB and then write the callsign.\nTo unbook a position, use `/unbook`."
        i = 1
        section_positions = {}
        for _ in range(section_amount):
            section_title = await StaffingAsync._setup_section(self, ctx, i)
            section_pos = await StaffingAsync._setup_section_pos(self, ctx, section_title)
            section_positions[section_title] = section_pos
            i += 1

        format_staffing_message = ""
        if format_staffing_message != "":
            format_staffing_message += "\n"

        formatted_date = dates[3].strftime("%A %d/%m/%Y")

        pos_data = ''
        for x in section_positions:
            pos_data += f'\n\n{x}:\n' + '\n' .join(position for position in section_positions[x]) + '\n'

        format_staffing_message += f'{title} staffing - {formatted_date} {dates[1]} - {dates[2]}z\n\n{description}\n{pos_data}'

        restrict_bookings = {
            'No': 0,
            'Yes': 1
        }

        msg = await channel.send(format_staffing_message)
        await msg.pin()
        await channel.purge(limit=None, check=lambda msg: not msg.pinned)
        StaffingDB.insert(self=self, table="staffing", columns=['title', 'date', 'description', 'channel_id', 'message_id', 'week_interval', 'restrict_bookings'], values=[str(title), str(dates[0]), str(description), str(channel.id), str(msg.id), str(week_int), str(restrict_bookings[restrict_booking])])
        
        columns =  {
            1: 'main_pos_title',
            2: 'secondary_pos_title',
            3: 'regional_pos_title'
        }
        j = 1
        for x in section_positions:
            StaffingDB.update(self=self, table="staffing", columns=[columns[j]], values={columns[j]: x}, where=["title"], value={"title": title})
            for pos in section_positions[x]:
                StaffingDB.insert(self=self, table="positions", columns=['position', 'user', 'type', 'title'], values=[pos, "", j, title])
            j += 1

    @app_commands.command(name="refreshevent", description="Bot refreshes selected event")
    @app_commands.describe(title="Which staffing would you like to refresh?")
    @app_commands.checks.has_any_role(*staff_roles())
    async def refreshevent(self, interaction: discord.Integration, title: StaffingAsync._get_avail_titles()):
        await StaffingAsync._updatemessage(self, title)
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx
        await ctx.send(f"{ctx.author.mention} Event `{title}` has been refreshed", delete_after=5, ephemeral=True)

    @app_commands.command(name="manreset", description="Bot manually resets selected event")
    @app_commands.describe(title="Which staffing would you like to manually reset?")
    @app_commands.checks.has_any_role(*staff_roles())
    async def manreset(self, interaction: discord.Integration, title: StaffingAsync._get_avail_titles()):
        await self.bot.wait_until_ready()
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx
        try:
            staffing = StaffingDB.select(table='staffing', columns=['*'], where=['title'], value={'title': title})
            title = staffing[1]
            week = staffing[6]
            
            await ctx.send(f"{ctx.author.mention} Started manual reset of `{title}` at `{str(datetime.now().isoformat())}`", delete_after=5, ephemeral=True)

            StaffingDB.update(self=self, table='positions', where=['title'], value={'title': title}, columns=['user'], values={'user': ''})
            newdate = await StaffingAsync._geteventdate(self=self, title=title, interval=week)

            StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': title}, columns=['date'], values={'date': newdate[0]})
            await StaffingAsync._updatemessage(self=self, title=title)

            channel = self.bot.get_channel(int(staffing[4]))
            await channel.send("The chat is being automatic reset!")
            await asyncio.sleep(5)
            await channel.purge(limit=None, check=lambda msg: not msg.pinned)

            await ctx.send(f"{ctx.author.mention} Finished manual reset of `{title}` at `{str(datetime.now().isoformat())}`", delete_after=5, ephemeral=True)
        except Exception as e:
            await ctx.send(f"{ctx.author.mention} The bot failed to manual reset `{title}` with error `{e}` at `{str(datetime.now().isoformat())}`", ephemeral=True)

    @app_commands.command(name="updatestaffing", description="Bot updates selected staffing")
    @app_commands.describe(title="Which staffing would you like to update?")
    @app_commands.checks.has_any_role(*staff_roles())
    async def updatestaffing(self, interaction: discord.Integration, title: StaffingAsync._get_avail_titles()):
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx
        try:
            await ctx.send('Select an option', view=SelectView(title=title, ctx=ctx, bot=self.bot))
        except Exception as e:
            await ctx.send(f'Error updating staffing {title} - {e}')
            raise e

    @app_commands.command(name="book", description="Bot books selected position for selected staffing")
    @app_commands.describe(position="Which position would you like to book?")
    @app_commands.checks.has_any_role(*controller_roles())
    async def book(self, interaction: discord.Integration, position: str):
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx
        try:
            vatsim_member = discord.utils.get(ctx.guild.roles, id=VATSIM_MEMBER_ROLE)
            vatsca_member = discord.utils.get(ctx.guild.roles, id=VATSCA_MEMBER_ROLE)
            usernick = ctx.author.id
            if vatsim_member in ctx.author.roles or vatsca_member in ctx.author.roles:
                
                event_channel = StaffingDB.select(table='staffing', columns=['channel_id'], amount="all")
                title = StaffingDB.select(table='staffing', columns=['title'], where=['channel_id'], value={'channel_id': ctx.channel.id})
                positions = StaffingDB.select(table='positions', columns=['position', 'user'], where=['title'], value={'title': title[0]}, amount='all')
                main_pos = StaffingDB.select(table="positions", columns=['position', 'user'], where=['title', 'type'], value={'title': title[0], 'type': 'main'}, amount='all')
                sec_pos = StaffingDB.select(table="positions", columns=['position', 'user'], where=['title', 'type'], value={'title': title[0], 'type': 'secondary'}, amount='all')
                reg_pos = StaffingDB.select(table="positions", columns=['position', 'user'], where=['title', 'type'], value={'title': title[0], 'type': 'regional'}, amount='all')
                eventDetails = StaffingDB.select(table='staffing', columns=['date', 'restrict_bookings'], where=['title'], value={'title': title[0]})
                
                if any(ctx.channel.id in channel for channel in event_channel):
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

    @app_commands.command(name="unbook", description="Bot unbooks selected position for selected staffing")
    async def unbook(self, interaction: discord.Integration):
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx
        try:
            event_channel = StaffingDB.select(table='staffing', columns=['channel_id'], amount='all')
            title = StaffingDB.select(table='staffing', columns=['title'], where=['channel_id'], value={'channel_id': ctx.channel.id})
            positions = StaffingDB.select(table='positions', columns=['position', 'user'], where=['title'], value={'title': title[0]}, amount='all')
            usernick = ctx.author.id
            if any(ctx.channel.id in channel for channel in event_channel):
                if any(f'<@{usernick}>' in match for match in positions):

                    cid = re.findall("\d+", str(ctx.author.nick))

                    position = StaffingDB.select(table='positions', columns=['position'], where=['user', 'title'], value={'user': f'<@{usernick}>', 'title': title[0]})

                    request = await Booking.delete_booking(self, int(cid[0]), str(position[0]))
                    if request == 200:
                        StaffingDB.update(self=self, table='positions', columns=['user'], values={'user': ''}, where=['user', 'title'], value={'user': f'<@{usernick}>', 'title': title[0]})
                        await StaffingAsync._updatemessage(self, title[0])
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
    # TASK LOOP FUNCTION
    # ----------------------------------
    #
    @tasks.loop(seconds=STAFFING_INTERVAL)
    async def autoreset(self, override=False):
        await self.bot.wait_until_ready()
        if DEBUG == True and override == False:
                print("autoreset skipped due to DEBUG ON. You can start manually with command instead.")
                return
        staffings = StaffingDB.select(table='staffing', columns=['*'], amount='all')
        now = datetime.utcnow()
        for staffing in staffings:
            title = staffing[1]
            date = staffing[2]
            week = staffing[6]
            if now.date() > date:
                print(f"Started autoreset of {title} at {str(datetime.now().isoformat())}")
                StaffingDB.update(self=self, table='positions', where=['title'], value={'title': title}, columns=['user'], values={'user': ''})
                newdate = await StaffingAsync._geteventdate(self=self, title=title, interval=week)
                StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': title}, columns=['date'], values={'date': newdate[0]})
                await StaffingAsync._updatemessage(self=self, title=title)
                channel = self.bot.get_channel(int(staffing[4]))
                await channel.send("The chat is being automatic reset!")
                await asyncio.sleep(5)
                await channel.purge(limit=None, check=lambda msg: not msg.pinned)

                print(f"Finished autoreset of {title} at {str(datetime.now().isoformat())}")



        



async def setup(bot):
    await bot.add_cog(StaffingCog(bot))