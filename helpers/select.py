import discord, asyncio
from discord.ext import commands
from helpers.staffing_async import StaffingAsync
from helpers.staffing_db import StaffingDB

class Select(discord.ui.Select):
    def __init__(self, title = None, ctx = None, bot = None) -> None:
        options=[
            discord.SelectOption(label="Event interval", emoji="🗓️", description="Update the event interval"),
            discord.SelectOption(label="Staffing message", emoji="💬", description="Update the staffing message"),
            discord.SelectOption(label="Sections & Positions", emoji="📰", description="Update the different section and positions"),
            discord.SelectOption(label="Booking restriction", emoji="📅", description="Change booking restriction"),
            discord.SelectOption(label="Delete Staffing", emoji="❌", description="Delete Staffing"),
            ]
        super().__init__(placeholder="Select an option", max_values=1, min_values=1, options=options)
        self.title = title
        self.ctx = ctx
        self.bot = bot

    async def callback(self, interaction: discord.Integration) -> None:
        if self.values[0] == "Event interval":
            await interaction.response.defer()
            week_int = await StaffingAsync._get_interval(self, self.ctx)
            dates = await StaffingAsync._geteventdate(self, self.title)
            StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': self.title}, columns=['week_interval', 'date'], values={'week_interval': week_int, 'date': dates[0]})
            await StaffingAsync._updatemessage(self=self, title=self.title)
            await interaction.followup.send(f'Event week interval updated to - `{week_int}`')
        elif self.values[0] == "Staffing message":
            await interaction.response.defer()
            newdescription = await StaffingAsync._get_description(self, self.ctx)
            newdescription = newdescription + "\n\nTo book a position, write `/book`, press TAB and then write the callsign.\nTo unbook a position, use `/unbook`."
            StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': self.title}, columns=['description'], values={'description': newdescription})
            await StaffingAsync._updatemessage(self=self, title=self.title)
            await interaction.followup.send(f'Event description/staffing message has been updated to:\n{newdescription}')
        elif self.values[0] == "Sections & Positions":
            await interaction.response.defer()
            section = await StaffingAsync._section_type(self, self.ctx)
            section_title = await StaffingAsync._setup_section(self, self.ctx, section)
            positions = StaffingDB.select(table='positions', columns=['position'], where=['type', 'title'], value={'type': section, 'title': self.title})
            if section_title != 'None':
                section_pos = await StaffingAsync._setup_section_pos(self, self.ctx, section_title)
            columns = {
                1: 'main_pos_title',
                2: 'secondary_pos_title',
                3: 'regional_pos_title'
            }
            StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': self.title}, columns=[columns[int(section)]], values={columns[int(section)]: section_title})
            if positions != 'None':
                StaffingDB.delete(self=self, table='positions', where=['type', 'title'], value={'type' : section, 'title' : self.title})

            if section_title != 'None':
                for position in section_pos:
                    StaffingDB.insert(self=self, table="positions", columns=['position', 'user', 'type', 'title'], values=[position, "", section, self.title])
            
                formatted_pos_data = "\n" .join(
                            position for position in section_pos)
                await interaction.followup.send(f'Section Title updated to `{section_title}`\n\nPositions updated to:\n{formatted_pos_data}')
            else:
                await interaction.followup.send(f'Section has been removed.')
            await StaffingAsync._updatemessage(self=self, title=self.title)
        elif self.values[0] == "Booking restriction":
            await interaction.response.defer()
            restriction = await StaffingAsync._get_retriction(self=self, ctx=self.ctx)
            restrict_bookings = {
                'No': 0,
                'Yes': 1
            }
            StaffingDB.update(self=self, table='staffing', where=['title'], value={'title': self.title}, columns=['restrict_bookings'], values={'restrict_bookings': restrict_bookings[restriction]})
            await interaction.followup.send(f'Booking restriction updated.')
        elif self.values[0] == "Delete Staffing":
            await interaction.response.defer()
            confirm_delete = await StaffingAsync._getconfirmation(self, self.ctx, self.title)
            if confirm_delete == self.title:
                event = StaffingDB.select(table='staffing', columns=['channel_id', 'message_id'], where=['title'], value={'title': self.title})
                channel_id = event[0]
                message_id = event[1]
                channel = self.bot.get_channel(int(channel_id))
                message = await channel.fetch_message(int(message_id))
                await message.delete()
                StaffingDB.delete(self=self, table='staffing', where=['title'], value={ 'title' : self.title, })
                StaffingDB.delete(self=self, table='positions', where=['title'], value={ 'title' : self.title, })

                await interaction.followup.send(f'Staffing for `{self.title}` has been deleted')
            elif confirm_delete == 'CANCEL':
                await interaction.followup.send(f'Deletion of `{self.title}` has been cancelled.')


class SelectView(discord.ui.View):
    def __init__(self, *, timeout = 180, title = None, ctx = None, bot = None):
        super().__init__(timeout=timeout)
        self.add_item(Select(title=title, ctx=ctx, bot=bot))