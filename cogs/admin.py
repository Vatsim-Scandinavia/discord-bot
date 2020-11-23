import os

from discord.ext import commands

from helpers.message import roles


class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Hidden means it won't show up on the default help.
    @commands.command(name='load', hidden=True)
    @commands.has_any_role(*roles())
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
    @commands.has_any_role(*roles())
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
    @commands.has_any_role(*roles())
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
    @commands.has_any_role(*roles())
    async def ping(self, ctx):
        """
        Function sends pong if member has any of the admin roles
        :param ctx:
        :return None:
        """
        await ctx.send('Pong')

    @commands.command(name='say')
    @commands.has_any_role(*roles())
    async def say(self, ctx, *, content: str) -> None:
        """
        Bot sends a specific message sent by user
        :param ctx:
        :param content:
        :return None:
        """
        await ctx.message.delete()
        await ctx.send(content)

    @commands.command(name='delete', aliases=['purge'])
    @commands.has_any_role(*roles())
    async def delete(self, ctx, *, number: int = 0):
        """
        Function deletes specific amount of messages
        :param ctx:
        :param number:
        :return None:
        :raise Exception:
        """
        if os.getenv('DEBUG') == 'True':
            try:
                msg_delete = []
                async for msg in ctx.channel.history(limit=number):
                    msg_delete.append(msg)

                await ctx.message.channel.delete_messages(msg_delete)
            except Exception as exception:
                await ctx.send(exception)
        else:
            await ctx.message.delete()
            await ctx.author.send('Command is disabled because debug is not enabled.')


def setup(bot):
    bot.add_cog(AdminCog(bot))
