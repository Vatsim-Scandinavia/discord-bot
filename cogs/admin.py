import discord

from discord.ext import commands
from discord import app_commands
from helpers.message import staff_roles, embed
from helpers.config import COGS_LOAD, GUILD_ID, DEBUG


class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    guild_ids = [GUILD_ID]

    async def handle_cog_action(self, action: str, interaction: discord.Interaction, cog: str) -> None:
        try:
            if action == 'load':
                self.bot.load_extension(COGS_LOAD[cog])
            
            elif action == 'unload':
                self.bot.unload_extension(COGS_LOAD[cog])

            elif action == 'reload':
                self.bot_load_extension(COGS_LOAD[cog])
                self.bot.unload_extension(COGS_LOAD[cog])
        
        except Exception as e:
            await interaction.response.send_message(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await interaction.response.send_message('**`SUCCESS`**')

    # Hidden means it won't show up on the default help.
    @app_commands.command(name="load", description="Command which Loads a Module.")
    @app_commands.checks.has_any_role(*staff_roles())
    async def load(self, interaction: discord.Interaction, *, cog: str):
        """
            Command which Loads a Module.
        """
        await self.handle_cog_action('load', interaction, cog)

    @app_commands.command(name="unload", description="Command which Unloads a Module.")
    @app_commands.checks.has_any_role(*staff_roles())
    async def unload(self, interaction: discord.Interaction, *, cog: str):
        """
            Command which Unloads a Module.
        """
        await self.handle_cog_action('unload', interaction, cog)

    @app_commands.command(name="reload", description="Command which Reloads a Module.")
    @app_commands.checks.has_any_role(*staff_roles())
    async def reload(self, interaction: discord.Interaction, *, cog: str):
        """
            Command which Reloads a Module.
        """
        await self.handle_cog_action('reload', interaction, cog)

    @app_commands.command(name="cogs", description="Command which sends a message with all available cogs.")
    @app_commands.checks.has_any_role(*staff_roles())
    async def cogs(self, interaction: discord.Interaction):
        """
            Command which sends a message with all available cogs.
        """

        fields = [{'name': key, 'value': COGS_LOAD[key]} for key in COGS_LOAD]

        msg = embed(title="List of Cogs", description="All available cogs", fields=fields)

        await interaction.response.send_message(embed=msg)
    
    @app_commands.command(name="ping", description="Function sends pong if member has any of the admin roles.")
    @app_commands.checks.has_any_role(*staff_roles())
    async def ping(self, interaction: discord.Interaction): 
        """
        Function sends pong if member has any of the admin roles
        :param ctx:
        :return None:
        """
        await interaction.response.send_message('Pong')

    @app_commands.command(name="say", description="Bot sends a specific message sent by user.")
    @app_commands.checks.has_any_role(*staff_roles())
    async def say(self, interaction: discord.Interaction, *, content: str) -> None:
        """
        Bot sends a specific message sent by user
        :param ctx:
        :param content:
        :return None:
        """
        await interaction.response.send_message(content)

    @app_commands.command(name="delete", description="Function deletes specific amount of messages.")
    @app_commands.checks.has_any_role(*staff_roles())
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
        if DEBUG:
            try:
                await ctx.channel.purge(limit=number)
                await ctx.send(f"Deleted {number} messages.", delete_after=5)

            except Exception as exception:
                await ctx.send(f"An error occurred: {exception}")
        else:
            await ctx.send('Command is disabled because debug is not enabled.', ephemeral=True)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
