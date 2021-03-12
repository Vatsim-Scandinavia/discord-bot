from helpers.config import GUILD_ID
import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from helpers.message import embed


class MemberCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    guild_ids = [GUILD_ID]

    @cog_ext.cog_slash(name="test", guild_ids=guild_ids, description="Function sends example embed.")
    async def run_example_embed(self, ctx: SlashContext):
        await self.example_embed(ctx)
    
    @commands.command(name='embeds', aliases=['test'], brief='Function sends example embed.')
    @commands.guild_only()
    async def example_embed(self, ctx):
        """
        Function sends example embed
        :param ctx:
        :return:
        """
        message = embed(title='test', description='test')

        await ctx.send(embed=message)


def setup(bot):
    bot.add_cog(MemberCog(bot))
