import discord
from discord.ext import commands
from helpers.message import embed


class MemberCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='embeds', aliases=['test'])
    @commands.guild_only()
    async def example_embed(self, ctx):

        message = embed(title='test', description='test')
        
        await ctx.send(embed=message)


def setup(bot):
    bot.add_cog(MemberCog(bot))