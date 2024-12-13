import discord

from discord import app_commands
from discord.ext import commands

from helpers.message import embed
from helpers.handler import Handler
from helpers.config import config

class UpdateCountryMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_or_update_message(self, ctx, channel_id, message_id, title, content, author = None, text = None):
        """
        Handles sending or updating a message in a specified channel.

        Args:
            ctx: Context
            channel_id (int): The ID of the channel to send the message in.
            message_id (int): The ID of the existing message to update, or None for a new message.
            title (str): The title of the message.
            content (str): The content of the message.
            author (discord.User, optional): The author of the message. Defaults to None.
            text (str, optional): The text of the message. Defaults to None.
        """
        channel = discord.utils.get(ctx.guild.channels, id=channel_id)
        if not channel:
            await ctx.send(f"Channel with ID {channel_id} not found.", delete_after=5)
            return
        
        try:
            if message_id:
                message = await channel.fetch_message(int(message_id))
                if message:
                    await message.edit(content=text, embed=embed(title=title, description=content, author=author))
            else:
                await channel.send(content=text, embed=embed(title=title, description=content, author=author))
            await ctx.send("Message successfully updated.", delete_after=5)
            
        except Exception as e:
            print(f"Error updating message: {e}", flush=True)
            await ctx.send("An error occurred while updating the message.", delete_after=5)

    def read_file(self, filepath):
        """
        Reads content from a specified file and returns it as a string.
        """
        try:
            with open(filepath, 'r') as file:
                return file.read()
        except FileNotFoundError:
            print(f"File '{filepath}' not found.")
            return ""
        
    @app_commands.command(name="update", description="Post or update country-related messages.")
    @app_commands.choices(
        option=[
            app_commands.Choice(name="Channels", value="channels"),
            app_commands.Choice(name="Notifications", value="notifications"),
            app_commands.Choice(name="Welcome", value="welcome"),
            app_commands.Choice(name="Rules", value="rules"),
        ]
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def update(self, interaction: discord.Interaction, option: app_commands.Choice[str], message_id: str = None):
        ctx = await Handler.get_context(self, self.bot, interaction)
        await ctx.send("Processing request...", delete_after=5)

        author = {
            "name": self.bot.user.name,
            "url": config.DIVISION_URL,
            "icon": self.bot.user.avatar.url
        }
        
        if option.value == "channels":
            content = self.read_file("messages/countries.md")
            await self.send_or_update_message(self, ctx, config.ROLES_CHANNEL, message_id, "Available Channel Roles", content)

        elif option.value == "notifications":
            content = self.read_file("messages/notification.md")
            text = self.read_file("messages/notification_message.md")
            await self.send_or_update_message(ctx, config.ROLES_CHANNEL, message_id, "Available Country Roles", content, text=text)

        elif option.value == "welcome":
            content = self.read_file("messages/welcome.md")
            await self.send_or_update_message(ctx, config.WELCOME_CHANNEL, message_id, "Welcome", content, author=author)

        elif option.value == "rules":
            content = self.read_file("messages/rules.md")
            await self.send_or_update_message(ctx, config.RULES_CHANNEL, message_id, "Rules", content, author=author)

async def setup(bot):
    await bot.add_cog(UpdateCountryMessage(bot))
