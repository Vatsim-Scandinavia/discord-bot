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
        await ctx.message.delete()
        await ctx.send(content)

    @commands.command(name='delete', aliases=['purge'])
    @commands.has_any_role('web team', 'admin')
    async def delete(self, ctx, *, number: int = 0):
        try:
            msg_delete = []
            async for msg in ctx.channel.history(limit=number):
                msg_delete.append(msg)

            await ctx.message.channel.delete_messages(msg_delete)
        except Exception as exception:
            await ctx.send(exception)
def setup(bot):
    bot.add_cog(AdminCog(bot))