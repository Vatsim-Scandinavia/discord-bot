import discord
from discord.ext import commands
from discord import app_commands
from helpers.config import config
from helpers.message import embed
from helpers.handler import Handler


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # autocomplete is not done yet. It returns weird result consider another metod - TBD
    async def autocomplete_loaded_cogs(
        self, interaction: discord.Interaction, current: str
    ):
        # Get all loaded cog names
        loaded_cogs = [key for key in config.COGS_LOAD.keys()]

        # Provide a filtered list of options as user types
        return [
            app_commands.Choice(name=cog, value=cog)
            for cog in loaded_cogs
            if current.lower() in cog.lower()
        ]

    async def autocomplete_unloaded_cogs(
        self, interaction: discord.Interaction, current: str
    ):
        all_cogs = [cog.split('.')[-1] for cog in config.COGS]
        loaded_cogs = [cog for cog in interaction.client.cogs]
        unloaded_cogs = [cog for cog in all_cogs if cog not in loaded_cogs]

        return [
            app_commands.Choice(name=cog, value=cog)
            for cog in unloaded_cogs
            if current.lower() in cog.lower()
        ]

    @app_commands.command(name='load', description='Command which Loads an extention')
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    @app_commands.autocomplete(cog=autocomplete_unloaded_cogs)
    async def load(self, interaction: discord.Interaction, cog: str):
        try:
            await self.bot.load_extension(config.COGS_LOAD[cog])

        except Exception as e:
            await interaction.response.send_message(
                f'**`ERROR:`** {type(e).__name__} - {e}'
            )

        else:
            await interaction.response.send_message('**`SUCCESS`**')

    @app_commands.command(
        name='unload', description='Command which Unloads an extention'
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    @app_commands.autocomplete(cog=autocomplete_loaded_cogs)
    async def unload(self, interaction: discord.Interaction, cog: str):
        print(cog, flush=True)
        try:
            await self.bot.unload_extension(config.COGS_LOAD[cog])

        except Exception as e:
            await interaction.response.send_message(
                f'**`ERROR:`** {type(e).__name__} - {e}'
            )

        else:
            await interaction.response.send_message('**`SUCCESS`**')

    @app_commands.command(
        name='reload', description='Command which Reloads an extention'
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    @app_commands.autocomplete(cog=autocomplete_loaded_cogs)
    async def reload(self, interaction: discord.Interaction, cog: str):
        try:
            await self.bot.unload_extension(config.COGS_LOAD[cog])
            await self.bot.load_extension(config.COGS_LOAD[cog])

        except Exception as e:
            await interaction.response.send_message(
                f'**`ERROR:`** {type(e).__name__} - {e}'
            )

        else:
            await interaction.response.send_message('**`SUCCESS`**')

    @app_commands.command(
        name='cogs',
        description='Command which sends a message with all available cogs.',
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def cogs(self, interaction: discord.Interaction):
        """
        Command which sends a message with all available cogs.
        """

        fields = [
            {'name': key, 'value': config.COGS_LOAD[key]} for key in config.COGS_LOAD
        ]

        msg = embed(
            title='List of Cogs', description='All available cogs', fields=fields
        )

        await interaction.response.send_message(embed=msg)

    @app_commands.command(
        name='ping',
        description='Function sends pong if member has any of the admin roles.',
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message('Pong')

    @app_commands.command(
        name='say', description='Bot sends a specific message sent by user.'
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def say(self, interaction: discord.Interaction, *, content: str):
        await interaction.channel.send(content)

    @app_commands.command(
        name='delete', description='Function deletes specific amount of messages.'
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def delete(self, interaction: discord.Interaction, amount: int):
        ctx = await Handler.get_context(self, self.bot, interaction)

        if config.DEBUG:
            try:
                await ctx.channel.purge(limit=amount)
                await ctx.send(f'Deleted {amount} messages.', delete_after=5)

            except Exception as exception:
                await ctx.send(f'An error occurred: {exception}')
        else:
            await ctx.send(
                'Command is disabled because debug is not enabled.', ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
