from helpers.config import GUILD_ID, DEBUG
import discord
from discord.ext import commands
from discord_slash import cog_ext
from helpers.message import embed
from discord_slash.utils.manage_commands import create_choice, create_option

import aiohttp
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
        if DEBUG == True:
            message = embed(title='test', description='test')
            
            await ctx.send(embed=message)
        else:
            await ctx.author.send('Command is disabled because debug is not enabled.')



    @cog_ext.cog_slash(name="metar", guild_ids=guild_ids, description="Get METAR for an airport",
    options=[
        create_option(
            name="airport",
            description="ICAO of airport",
            option_type=3,
            required=True,
        )
    ])
    @commands.guild_only()
    async def example_embed(self, ctx, airport: str):
        """
        Function send METAR of specified airport
        """

        async with aiohttp.ClientSession() as session:
            async with session.get("http://metar.vatsim.net" + "/" + airport) as resp:
                
                if resp.status == 404:
                    return False
                
                metar_data = await resp.text()

                message = embed(title='METAR for ' + str.upper(airport), description=metar_data)
                await ctx.author.send(embed=message)


def setup(bot):
    bot.add_cog(MemberCog(bot))
