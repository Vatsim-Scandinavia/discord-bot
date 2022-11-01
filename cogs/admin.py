import os
import datetime
import discord

from discord.ext import commands, tasks
from discord import app_commands
from helpers.message import staff_roles, embed
from helpers.config import COGS_LOAD, GUILD_ID, DEBUG


class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    guild_ids = [GUILD_ID]

    # Hidden means it won't show up on the default help.
    @app_commands.command(name="load", description="Command which Loads a Module.")
    @commands.has_any_role(*staff_roles())
    async def load(self, interaction: discord.Interaction, *, cog: str):
        """
            Command which Loads a Module.
        """

        try:
            self.bot.load_extension(COGS_LOAD[cog])
        except Exception as e:
            await interaction.response.send_message.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await interaction.response.send_message.send('**`SUCCESS`**')

    @app_commands.command(name="unload", description="Command which Unloads a Module.")
    @commands.has_any_role(*staff_roles())
    async def unload(self, interaction: discord.Interaction, *, cog: str):
        """
            Command which Unloads a Module.
        """

        try:
            self.bot.unload_extension(COGS_LOAD[cog])
        except Exception as e:
            await interaction.response.send_message.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await interaction.response.send_message.send('**`SUCCESS`**')

    @app_commands.command(name="reload", description="Command which Reloads a Module.")
    @commands.has_any_role(*staff_roles())
    async def reload(self, interaction: discord.Interaction, *, cog: str):
        """
            Command which Reloads a Module.
        """

        try:
            self.bot.unload_extension(COGS_LOAD[cog])
            self.bot.load_extension(COGS_LOAD[cog])
        except Exception as e:
            await interaction.response.send_message.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await interaction.response.send_message.send('**`SUCCESS`**')

    @app_commands.command(name="cogs", description="Command which sends a message with all available cogs.")
    @commands.has_any_role(*staff_roles())
    async def cogs(self, interaction: discord.Interaction):
        """
            Command which sends a message with all available cogs.
        """

        fields = []

        for key in COGS_LOAD:
            fields.append({'name': key, 'value': COGS_LOAD[key]})

        msg = embed(title="List of Cogs", description="All available cogs", fields=fields)

        await interaction.response.send_message(embed=msg)
    
    @app_commands.command(name="ping", description="Function sends pong if member has any of the admin roles.")
    @commands.has_any_role(*staff_roles())
    async def ping(self, interaction: discord.Interaction): 
        """
        Function sends pong if member has any of the admin roles
        :param ctx:
        :return None:
        """
        await interaction.response.send_message('Pong')

    @app_commands.command(name="say", description="Bot sends a specific message sent by user.")
    @commands.has_any_role(*staff_roles())
    async def say(self, interaction: discord.Interaction, *, content: str) -> None:
        """
        Bot sends a specific message sent by user
        :param ctx:
        :param content:
        :return None:
        """
        await interaction.response.send_message("Message is being generated", delete_after=5)
        await interaction.response.send_message(content)

    @app_commands.command(name="delete", description="Function deletes specific amount of messages.")
    @commands.has_any_role(*staff_roles())
    async def delete(self, interaction: discord.Interaction, *, number: int = 0):
        """
        Function deletes specific amount of messages
        :param ctx:
        :param number:
        :return None:
        :raise Exception:
        """
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx
        if DEBUG == True:
            try:
                msg_delete = []
                async for msg in ctx.channel.history(limit=number):
                    msg_delete.append(msg)

                msgs = await ctx.send("Deleting messages")
                await msgs.channel.purge(limit=number)
            except Exception as exception:
                await ctx.send(exception)
        else:
            await ctx.send('Command is disabled because debug is not enabled.', ephemeral=True)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
