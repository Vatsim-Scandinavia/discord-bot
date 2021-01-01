from discord.ext import commands

from helpers.message import roles


class AnnouncementCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="announce", hidden=True)
    @commands.has_any_role(*roles())
    async def announce(self, ctx) -> None:

        """
        Function sends announcement message in specific channel
        :param ctx:
        :return:
        """

        channels = await self._get_channels(ctx)
        roles = await self._get_roles(ctx)
        message = await self._get_message(ctx)

        format_message = ""

        for role in roles:
            format_message += role.mention

        if format_message != "":
            format_message += "\n"

        format_message += message

        for channel in channels:
            await channel.send(format_message)

    async def _get_channels(self, ctx):
        """
        Function gets channels where it should send the announcement
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Awesome! Where would you like to post the announcement?')

            message = await self.bot.wait_for('message', timeout=60, check=lambda
                message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.channel_mentions) < 1:
                await ctx.send('Announcement canceled.')
                raise ValueError

            return message.channel_mentions
        except Exception as exception:
            await ctx.send(exception)
            raise exception

    async def _get_roles(self, ctx):
        """
        Function gets roles which should be pinged on announcement
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Which roles should be tagged?')

            message = await self.bot.wait_for('message', timeout=60, check=lambda
                message: message.author == ctx.author and ctx.channel == message.channel)

            return message.role_mentions
        except Exception as exception:
            await ctx.send(exception)
            raise exception

    async def _get_message(self, ctx):
        """
        Function gets a message that'll be included in announcement
        :param ctx:
        :return:
        """
        try:
            await ctx.send('Message?')
            message = await self.bot.wait_for('message', timeout=60, check=lambda
                message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Announcement cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as exception:
            await ctx.send(exception)
            raise exception


def setup(bot):
    bot.add_cog(AnnouncementCog(bot))
