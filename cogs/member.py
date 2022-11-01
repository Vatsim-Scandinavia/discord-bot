from helpers.config import DEBUG
import discord
from discord.ext import commands
from discord import app_commands
from helpers.message import embed

import aiohttp
import os


class MemberCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="test", description="Function sends example embed.")
    @commands.guild_only()
    async def example_embed(self, interaction: discord.Integration):
        """
        Function sends example embed
        :param ctx:
        :return:
        """
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx
        if DEBUG == True:
            message = embed(title='test', description='test')
            await ctx.send(embed=message)
        else:
            await ctx.send('Command is disabled because debug is not enabled.', ephemeral=True)



    @app_commands.command(name="metar", description="Get METAR for an airport")
    @commands.guild_only()
    async def example_embed(self, interaction: discord.Integration, airport: str):
        """
        Function send METAR of specified airport
        """

        async with aiohttp.ClientSession() as session:
            async with session.get("http://metar.vatsim.net" + "/" + airport) as resp:
                
                if resp.status == 404:
                    return False
                ctx: commands.Context = await self.bot.get_context(interaction)
                interaction._baton = ctx
                metar_data = await resp.text()

                message = embed(title='METAR for ' + str.upper(airport), description=metar_data)
                await ctx.send(embed=message, ephemeral=True)


async def setup(bot):
    await bot.add_cog(MemberCog(bot))
