import enum
from typing_extensions import Literal
import discord

from discord import app_commands, CategoryChannel, TextChannel
from discord.ext import commands, tasks

from datetime import datetime

from helpers.booking import Booking
from helpers.message import staff_roles
from helpers.staffing_async import StaffingAsync
from helpers.staffing_db import StaffingDB

class StaffingCog(commands.Cog):
    #
    # ----------------------------------
    # COG FUNCTIONS
    # ----------------------------------
    #

    def __init__(self, bot) -> None:
        self.bot = bot

    #
    # ----------------------------------
    # SLASH COMMAND FUNCTIONS
    # ----------------------------------
    #
    @app_commands.command(name="setupstaffing", description="Bot setups staffing information")
    @app_commands.describe(title="What should the title of the staffing be?", week_int="What should the week interval be? eg. 1 then the date will be selected each week.", section_amount="What should the section amount be? eg. 3 then there will be 3 sections.", restrict_booking="Should the staffing restrict booking to first section before allowing other sections too?")
    @commands.has_any_role(*staff_roles())
    async def setup_staffing(self, interaction: discord.Integration, title: StaffingAsync._get_titles(), week_int: app_commands.Range[int, 1, 4], section_amount: app_commands.Range[int, 1, 3], restrict_booking: Literal["Yes", "No"], channel: TextChannel):
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx
        dates = await StaffingAsync._geteventdate(self, title)
        description = await StaffingAsync._get_description(self, ctx)
        i = 1
        section_positions = {}
        for _ in range(section_amount):
            section_title = await StaffingAsync._setup_section(self, ctx, i)
            section_pos = await StaffingAsync._setup_section_pos(self, ctx, section_title)
            section_positions[section_title] = section_pos
            i += 1
        
        description = description + "\n\nTo book a position, write `/book`, press TAB and then write the callsign.\nTo unbook a position, use `/unbook`."

        format_staffing_message = ""
        if format_staffing_message != "":
            format_staffing_message += "\n"

        formatted_date = dates[0].strftime("%A %d/%m/%Y")

        format_staffing_message += f'{title} staffing - {formatted_date} {dates[1]} - {dates[2]}z\n\n{description}\n\n'

        for x in section_positions:
            description += f'{x}:\n' + '\n' .join(position for position in section_positions[x]) + '\n\n'

        msg = await channel.send(format_staffing_message)
        await msg.pin()
        await channel.purge(limit=None, check=lambda msg: not msg.pinned)
        StaffingDB.insert(self=self, table="staffing", columns=['title', 'date', 'description', 'channel_id', 'message_id', 'week_interval', 'restrict_bookings'], values=[str(title), str(dates[0]), str(description), str(channel.id), str(msg.id), str(week_int), str(restrict_booking)])
        
        columns = ['main_pos_title', 'secondary_pos_title', 'regional_pos_title']
        j = 0
        for x in section_positions:
            StaffingDB.update(self=self, table="staffing", columns=[columns[j]], values={columns[j]: section_positions[x]}, where=["title"], value={"title": title})
            for pos in section_positions[x]:
                StaffingDB.insert(self=self, table="positions", columns=['position', 'user', 'type', 'title'], values=[pos, "", j, title])
            j += 1
        await ctx.send(f"You've selected title: `{title}` & week interval: `{week_int}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StaffingCog(bot))