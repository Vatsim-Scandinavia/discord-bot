import discord

from discord.ext import commands

class Handler():
    
    def __init__(self) -> None:
        pass

    async def get_context(self, bot, interaction: discord.Interaction) -> commands.Context:
        """
        Helper function to get context from interaction
        """
        ctx: commands.Context = await bot.get_context(interaction)
        interaction,_baton = ctx
        return ctx