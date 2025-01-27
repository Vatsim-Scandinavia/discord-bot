import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from helpers.config import config
from helpers.handler import Handler
from helpers.message import embed


class MemberCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='test', description='Function sends example embed.')
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def test(self, interaction: discord.Interaction):
        ctx = await Handler.get_context(self, self.bot, interaction)

        if config.DEBUG:
            message = embed(title='test', description='test')
            await ctx.send(embed=message)
        else:
            await ctx.send(
                'Command is disabled because debug is not enabled.', ephemeral=True
            )

    @app_commands.command(name='metar', description='Get METAR for an airport')
    async def metar(self, interaction: discord.Interaction, airport: str) -> None:
        """Function send METAR of specified airport."""
        ctx = await Handler.get_context(self, self.bot, interaction)

        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://metar.vatsim.net/{airport}') as resp:
                if resp.status == 404:
                    await ctx.send(
                        f'No METAR found for airport `{airport}`.', ephemeral=True
                    )
                    return

                if resp.status != 200:
                    print(
                        f'An error occurred fetching METAR from `{airport}`\nResponse: {resp.status}'
                    )
                    await ctx.send(
                        f'Failed to fetch METAR. Error: {resp.status}', ephemeral=True
                    )
                    return

                metar_data = await resp.text()

                message = embed(
                    title='METAR for ' + str.upper(airport), description=metar_data
                )
                await ctx.send(embed=message, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(MemberCog(bot))
