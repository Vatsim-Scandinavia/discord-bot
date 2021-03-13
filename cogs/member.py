from helpers.config import GUILD_ID
import discord
from discord.ext import commands
from discord_slash import cog_ext
from helpers.message import embed

import os


class MemberCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    guild_ids = [GUILD_ID]

    
    @cog_ext.cog_slash(name="test", guild_ids=guild_ids, description="Function sends example embed.")
    @commands.guild_only()
    async def example_embed(self, ctx):
        """
        Function sends example embed
        :param ctx:
        :return:
        """
        if os.getenv('DEBUG') == 'True':
            message = embed(title='test', description='test')
            
            await ctx.send(embed=message)
        else:
            await ctx.author.send('Command is disabled because debug is not enabled.')


def setup(bot):
    bot.add_cog(MemberCog(bot))
