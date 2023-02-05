from datetime import date
from typing import Literal

from helpers.db import DB


class Staffing():
    #
    # ----------------------------------
    #   INITIAL
    # ----------------------------------
    #

    def __init__(self, id, title, date: date, description, channel_id: int, message_id: int, week_int: int, main_pos_title, secondary_pos_title, regional_pos_title, restrict_booking: int) -> None:
        """
        Create a staffing object
        """
        self.id = id
        self.title = title
        self.date = date
        self.description = description

        self.channel_id = channel_id
        self.message_id = message_id
        self.week_int = week_int
        self.main_pos_title = main_pos_title
        self.secondary_pos_title = secondary_pos_title 
        self.regional_pos_title = regional_pos_title

        self.restrict_booking = restrict_booking

    def _get_titles() -> Literal:
        events = DB.select(table='events', columns=[
                                'name'], amount='all')
        staffings = DB.select(
            table="staffing", columns=['title'], amount='all')
        formatted_staffings = []
        formatted_events = []

        if not events:
            formatted_events.append('None is available. Please try again later.')
        else:
            for staffing in staffings:
                formatted_staffings.append(" ".join(map(str, staffing)))

            for event in events:
                formatted_event = " ".join(map(str, event))
                if formatted_event not in formatted_staffings:
                    formatted_events.append(formatted_event)
        return Literal[tuple(formatted_events)]

    def _get_avail_titles() -> Literal:
        staffings = DB.select(table="staffing", columns=['title'], amount='all')
        formatted_staffings = []
        if not staffings:
            formatted_staffings.append('None is available. Please try again later.')
        else:
            for staffing in staffings:
                formatted_staffings.append(" ".join(map(str, staffing)))

        return Literal[tuple(formatted_staffings)]

    async def get_info(self, ctx, msg):
        try:
            await ctx.send(f'{msg} **FYI this command expires in 5 minutes**')
            message = await self.bot.wait_for('message', timeout=300, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as e:
            await ctx.send(f'Error getting the Staffing message - {e}')
            raise e

    async def get_int(self, ctx, msg, start: int, end: int):
        try:
            await ctx.send('Week interval? **FYI this command expires in 5 minutes**')
            message = await self.bot.wait_for('message', timeout=300, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Setup cancelled. No message was provided.')
                raise ValueError

            if int(message.content) not in range(1, 5):
                await ctx.send('The interval must be between 1 to 4')
                raise ValueError
        except Exception as e:
            await ctx.send(f'Error getting the Staffing message - {e}')
            raise e


