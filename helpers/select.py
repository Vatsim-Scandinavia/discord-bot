import discord
from helpers.staffing_async import StaffingAsync
from helpers.db import DB

class Select(discord.ui.Select):
    def __init__(self, id = None, ctx = None, bot = None) -> None:
        options=[
            discord.SelectOption(label="Event interval", emoji="🗓️", description="Update the event interval"),
            discord.SelectOption(label="Staffing message", emoji="💬", description="Update the staffing message"),
            discord.SelectOption(label="Sections & Positions", emoji="📰", description="Update the different section and positions"),
            discord.SelectOption(label="Booking restriction", emoji="📅", description="Change booking restriction"),
            discord.SelectOption(label="Delete Staffing", emoji="❌", description="Delete Staffing"),
            ]
        super().__init__(placeholder="Select an option", max_values=1, min_values=1, options=options)
        self.id = id
        self.ctx = ctx
        self.bot = bot

    async def callback(self, interaction: discord.Integration) -> None:
        title = DB.select(table="staffing", columns=['title'], where=['id'], value={'id': self.id})[0]
        if self.values[0] == "Event interval":
            await interaction.response.defer()
            week_int = await StaffingAsync._get_interval(self, self.ctx)
            dates = await StaffingAsync._geteventdate(self, self.id)
            DB.update(self=self, table='staffing', where=['id'], value={'id': self.id}, columns=['week_interval', 'date'], values={'week_interval': week_int, 'date': dates[0]})
            await StaffingAsync._updatemessage(self=self, id=self.id)
            await interaction.followup.send(f'Event week interval updated to - `{week_int}`')
        elif self.values[0] == "Staffing message":
            await interaction.response.defer()
            newdescription = await StaffingAsync._get_description(self, self.ctx)
            newdescription = newdescription + "\n\nTo book a position, write `/book`, press TAB and then write the callsign.\nTo unbook a position, use `/unbook`."
            DB.update(self=self, table='staffing', where=['id'], value={'id': self.id}, columns=['description'], values={'description': newdescription})
            await StaffingAsync._updatemessage(self=self, id=self.id)
            await interaction.followup.send(f'Event description/staffing message has been updated to:\n{newdescription}')
        elif self.values[0] == "Sections & Positions":
            await interaction.response.defer()
            check_pos = DB.select(table="positions", columns=['user'], where=['event'], value={'event': self.id}, amount='all')
            update_ok = True
            for pos in check_pos:
                if pos[0] != '':
                    update_ok = False

            if update_ok == True:
                section = await StaffingAsync._section_type(self, self.ctx)
                section_title = await StaffingAsync._setup_section(self, self.ctx, section)
                positions = DB.select(table='positions', columns=['position'], where=['type', 'event'], value={'type': section, 'event': self.id})
                if section_title != 'None':
                    section_pos = await StaffingAsync._setup_section_pos(self, self.ctx, section_title)
                columns = {
                    1: 'section_1_title',
                    2: 'section_2_title',
                    3: 'section_3_title',
                    4: 'section_4_title'
                }
                DB.update(self=self, table='staffing', where=['id'], value={'id': self.id}, columns=[columns[int(section)]], values={columns[int(section)]: section_title})
                if positions != 'None':
                    DB.delete(self=self, table='positions', where=['type', 'event'], value={'type' : section, 'event' : self.id})

                if section_title != 'None':
                    for item in section_pos:
                        local = {
                            True: 1,
                            False: 0,
                        }
                        DB.insert(self=self, table="positions", columns=['position', 'user', 'type', 'local_booking', 'start_time', 'end_time', 'event'], values=[section_pos[item]['position'], "", section, local[section_pos[item]['local_booking']], section_pos[item]['start_time'], section_pos[item]['end_time'], self.id])
                
                    formatted_pos_data = "\n" .join(
                                position for position in section_pos)
                    await interaction.followup.send(f'Section Title updated to `{section_title}`\n\nPositions updated to:\n{formatted_pos_data}')
                else:
                    await interaction.followup.send('Section has been removed.')
                await StaffingAsync._updatemessage(self=self, id=self.id)
            else:
                await interaction.followup.send('Update is not OK. There are still active bookings for this event.')
        elif self.values[0] == "Booking restriction":
            await interaction.response.defer()
            restriction = await StaffingAsync._get_retriction(self=self, ctx=self.ctx)
            restrict_bookings = {
                'no': 0,
                'yes': 1
            }
            DB.update(self=self, table='staffing', where=['id'], value={'id': self.id}, columns=['restrict_bookings'], values={'restrict_bookings': restrict_bookings[restriction]})
            await interaction.followup.send('Booking restriction updated.')
        elif self.values[0] == "Delete Staffing":
            await interaction.response.defer()
            confirm_delete = await StaffingAsync._getconfirmation(self, self.ctx, title)
            event = DB.select(table='staffing', columns=['title', 'channel_id', 'message_id'], where=['id'], value={'id': self.id})
            if confirm_delete == event[0]:
                channel_id = event[1]
                message_id = event[2]
                channel = self.bot.get_channel(int(channel_id))
                message = await channel.fetch_message(int(message_id))
                await message.delete()
                DB.delete(self=self, table='staffing', where=['id'], value={'id': self.id})
                DB.delete(self=self, table='positions', where=['event'], value={'event': self.id})

                await interaction.followup.send(f'Staffing for `{event[0]}` has been deleted')
            elif confirm_delete == 'CANCEL':
                await interaction.followup.send(f'Deletion of `{event[0]}` has been cancelled.')


class SelectView(discord.ui.View):
    def __init__(self, *, timeout = 180, id = None, ctx = None, bot = None):
        super().__init__(timeout=timeout)
        self.add_item(Select(id=id, ctx=ctx, bot=bot))