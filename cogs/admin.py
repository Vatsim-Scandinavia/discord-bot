import os
import datetime
import asyncio

from discord.ext import commands, tasks
from discord_slash import cog_ext, SlashContext
from helpers.message import roles, embed
from helpers.config import COGS_LOAD, GUILD_ID, BOT_CHANNEL, STAFFING_INTERVAL, DEBUG


class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.reload_staffing.start()

    def cog_unload(self):
        self.reload_staffing.cancel()

    guild_ids = [GUILD_ID]

    # Hidden means it won't show up on the default help.
    @cog_ext.cog_slash(name="load", guild_ids=guild_ids, description="Command which Loads a Module.")
    @commands.has_any_role(*roles())
    async def load(self, ctx: SlashContext, *, cog: str):
        """
            Command which Loads a Module.
        """

        try:
            self.bot.load_extension(COGS_LOAD[cog])
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @cog_ext.cog_slash(name="unload", guild_ids=guild_ids, description="Command which Unloads a Module.")
    @commands.has_any_role(*roles())
    async def unload(self, ctx: SlashContext, *, cog: str):
        """
            Command which Unloads a Module.
        """

        try:
            self.bot.unload_extension(COGS_LOAD[cog])
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @cog_ext.cog_slash(name="reload", guild_ids=guild_ids, description="Command which Reloads a Module.")
    @commands.has_any_role(*roles())
    async def reload(self, ctx: SlashContext, *, cog: str):
        """
            Command which Reloads a Module.
        """

        try:
            self.bot.unload_extension(COGS_LOAD[cog])
            self.bot.load_extension(COGS_LOAD[cog])
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @tasks.loop(seconds=STAFFING_INTERVAL)
    async def reload_staffing(self):
        """
            Command which Reloads a Module.
        """
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        channel = self.bot.get_channel(int(BOT_CHANNEL))

        try:
            if now.weekday() == 0 and now.hour == 23 and 00 <= now.minute <= 00:
                self.bot.unload_extension(COGS_LOAD["staffing"])
                self.bot.load_extension(COGS_LOAD["staffing"])
        except Exception as e:
            await channel.send(f'**`ERROR:`** {type(e).__name__} - {e}')

    @cog_ext.cog_slash(name="cogs", guild_ids=guild_ids, description="Command which sends a message with all available cogs.")
    @commands.has_any_role(*roles())
    async def cogs(self, ctx: SlashContext):
        """
            Command which sends a message with all available cogs.
        """

        fields = []

        for key in COGS_LOAD:
            fields.append({'name': key, 'value': COGS_LOAD[key]})

        msg = embed(title="List of Cogs", description="All available cogs", fields=fields)

        await ctx.send(embed=msg)
    
    @cog_ext.cog_slash(name="ping", guild_ids=guild_ids, description="Function sends pong if member has any of the admin roles.")
    @commands.has_any_role(*roles())
    async def ping(self, ctx: SlashContext): 
        """
        Function sends pong if member has any of the admin roles
        :param ctx:
        :return None:
        """
        await ctx.send('Pong')

    @cog_ext.cog_slash(name="say", guild_ids=guild_ids, description="Bot sends a specific message sent by user.")
    @commands.has_any_role(*roles())
    async def say(self, ctx: SlashContext, *, content: str) -> None:
        """
        Bot sends a specific message sent by user
        :param ctx:
        :param content:
        :return None:
        """
        msg = await ctx.send("Message is being generated")
        await asyncio.sleep(5)
        await msg.delete()
        await ctx.send(content)

    @cog_ext.cog_slash(name="delete", guild_ids=guild_ids, description="Function deletes specific amount of messages.")
    @commands.has_any_role(*roles())
    async def delete(self, ctx, *, number: int = 0):
        """
        Function deletes specific amount of messages
        :param ctx:
        :param number:
        :return None:
        :raise Exception:
        """
        if DEBUG == True:
            try:
                msg_delete = []
                async for msg in ctx.channel.history(limit=number):
                    msg_delete.append(msg)

                """await ctx.message.channel.delete_messages(msg_delete)"""
                msgs = await ctx.send("Deleting messages")
                await msgs.channel.purge(limit=number)
            except Exception as exception:
                await ctx.send(exception)
        else:
            await ctx.author.send('Command is disabled because debug is not enabled.')


def setup(bot):
    bot.add_cog(AdminCog(bot))
