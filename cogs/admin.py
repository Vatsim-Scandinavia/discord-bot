from discord.ext import commands
from asyncio import sleep

class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    # Hidden means it won't show up on the default help.
    @commands.command(name='load', hidden=True)
    @commands.has_any_role('web team', 'admin')
    async def load(self, ctx, *, cog: str):
        """
            Command which Loads a Module.
        """

        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='unload', hidden=True)
    @commands.has_any_role('web team', 'admin')
    async def unload(self, ctx, *, cog: str):
        """
            Command which Unloads a Module.
        """

        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='reload', hidden=True)
    @commands.has_any_role('web team', 'admin')
    async def reload(self, ctx, *, cog: str):
        """
            Command which Reloads a Module.
        """

        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='ping')
    @commands.has_any_role('web team', 'admin')
    async def ping(self, ctx):
        await ctx.send('Pong')

    @commands.command(name='say')
    @commands.has_any_role('web team', 'admin')
    async def say(self, ctx, *, content: str) -> None:
        await ctx.send(content)

    @commands.command(name="announce")
    @commands.has_any_role('web team', 'admin')
    async def announce(self, ctx) -> None:
        
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
        try:
            await ctx.send('Awesome! Where would you like to post the announcement?')

            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.channel_mentions) < 1:
                await ctx.send('Announcement cancled.')
                raise ValueError

            return message.channel_mentions
        except Exception as exception:
            await ctx.send(exception)
            raise exception

    async def _get_roles(self, ctx):
        try:
            await ctx.send('Which roles should be tagged?')
            
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            return message.role_mentions
        except Exception as exception:
            await ctx.send(exception)
            raise exception

    async def _get_message(self, ctx):
        try:
            await ctx.send('Message?')
            message = await self.bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

            if len(message.content) < 1:
                await ctx.send('Announcement cancelled. No message was provided.')
                raise ValueError

            return message.content
        except Exception as exception:
            await ctx.send(exception)
            raise exception

def setup(bot):
    bot.add_cog(AdminCog(bot))