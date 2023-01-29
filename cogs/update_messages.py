from secrets import choice
import discord

from discord import app_commands
from discord.ext import commands

from helpers.config import ROLES_CHANNEL, GUILD_ID, RULES_CHANNEL, DIVISION_URL, WELCOME_CHANNEL
from helpers.message import embed
from helpers.message import staff_roles


class UpdateCountryMessage(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    guild_ids = [GUILD_ID]
    

    @app_commands.command(name="update", description="Function posts updated countries message.")
    @app_commands.choices(option=[
        app_commands.Choice(name="Channels", value="1"),
        app_commands.Choice(name="Notifications", value="2"),
        app_commands.Choice(name="Welcome", value="3"),
        app_commands.Choice(name="Rules", value="4")
    ])
    @app_commands.checks.has_any_role(*staff_roles())
    async def update(self, interaction: discord.Integration, *, message_id: str = None, option: app_commands.Choice[str]):
        """
        Function posts updated countries message
        :param ctx:
        :param message_id:
        :return:
        """
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx 
        if option.value == "1":
            channel = discord.utils.get(ctx.guild.channels, id=ROLES_CHANNEL)
            if channel:
                author = {
                    'name': self.bot.user.name,
                    'url': DIVISION_URL,
                    'icon': self.bot.user.display_avatar,
                }
                if message_id is None:
                    try:
                        await ctx.send("Message is being generated", delete_after=5)
                        text = self._read_file()
                        msg = embed(title='Available Channel Roles', description=text)
                        await channel.send(embed=msg)
                    except Exception as e:
                        print(e)
                else:
                    message_id = int(message_id)
                    message = await ctx.fetch_message(message_id)
                    
                    if message:
                        try:
                            await ctx.send("Message is being generated", delete_after=5)
                            text = self._read_file()
                            msg = embed(title='Available Channel Roles', description=text)
                            await message.edit(embed=msg)
                        except Exception as e:
                            print(e)
        
        elif option.value == "2":
            """
            Function posts updated countries message
            :param ctx:
            :param message_id:
            :return:
            """
            channel = discord.utils.get(ctx.guild.channels, id=ROLES_CHANNEL)
        
            if channel:
                author = {
                    'name': self.bot.user.name,
                    'url': DIVISION_URL,
                    'icon': self.bot.user.avatar_url,
                }
                if message_id is None:
                    try:
                        await ctx.send("Message is being generated", delete_after=5)
                        embd = self._read_embed__file()
                        text = self._read_message_file()
                        msg = embed(title='Available Country Roles', description=embd)
                        await channel.send(text, embed=msg)
                    except Exception as e:
                        print(e)
                else:
                    message_id = int(message_id)
                    message = await ctx.fetch_message(message_id)
        
                    if message:
                        try:
                            await ctx.send("Message is being generated", delete_after=5)
                            embd = self._read_embed__file()
                            text = self._read_message_file()
                            msg = embed(title='Available Country Roles', description=embd)
                            await message.edit(content=text, embed=msg)
                        except Exception as e:
                            print(e)
        elif option.value == "3":
            """
            Function posts updated welcome
            :param ctx:
            :param message_id:
            :return:
            """
            channel = discord.utils.get(ctx.guild.channels, id=WELCOME_CHANNEL)
            if channel:
                author = {
                    'name': self.bot.user.name,
                    'url': DIVISION_URL,
                    'icon': self.bot.user.avatar_url,
                }
                if message_id is None:
                    try:
                        await ctx.send("Message is being generated", delete_after=5)
                        text = self._read_welcome_file()
                        msg = embed(title='Welcome', description=text, author=author)
                        await channel.send(embed=msg)
                    except Exception as e:
                        print(e)
                else:
                    message_id = int(message_id)
                    message = await ctx.fetch_message(message_id)
    
                    if message:
                        try:
                            await ctx.send("Message is being generated", delete_after=5)
                            text = self._read_welcome_file()
                            msg = embed(title='Welcome', description=text, author=author)
                            await message.edit(embed=msg)
                        except Exception as e:
                            print(e)
        elif option.value == "4":
            """
            Function posts updated rules
            :param ctx:
            :param message_id:
            :return:
            """
            channel = discord.utils.get(ctx.guild.channels, id=RULES_CHANNEL)
            if channel:
                author = {
                    'name': self.bot.user.name,
                    'url': DIVISION_URL,
                    'icon': self.bot.user.avatar_url,
                }
                if message_id is None:
                    try:
                        await ctx.send("Message is being generated", delete_after=5)
                        text = self._read_rules_file()
                        msg = embed(title='Rules', description=text, author=author)
                        await channel.send(embed=msg)
                    except Exception as e:
                        print(e)
                else:
                    message_id = int(message_id)
                    message = await ctx.fetch_message(message_id)
    
                    if message:
                        try:
                            await ctx.send("Message is being generated", delete_after=5)
                            text = self._read_rules_file()
                            msg = embed(title='Rules', description=text, author=author)
                            await message.edit(embed=msg)
                        except Exception as e:
                            print(e)


    def _read_file(self) -> str:
        """
        Function reads and returns welcome and rules message stored in countries.md
        :return:
        """
        file = open('messages/countries.md', mode='r')
        data = file.read()
        file.close()
        return data

    def _read_embed__file(self) -> str:
        """
        Function reads and returns welcome and rules message stored in countries.md
        :return:
        """
        file = open('messages/notification.md', mode='r')
        data = file.read()
        file.close()
        return data

    def _read_message_file(self) -> str:
        """
        Function reads and returns welcome and rules message stored in countries.md
        :return:
        """
        file = open('messages/notification_message.md', mode='r')
        data = file.read()
        file.close()
        return data
    def _read_welcome_file(self) -> str:
        """
        Function reads and returns welcome and welcome message stored in welcome.md
        :return:
        """
        file = open('messages/welcome.md', mode='r')
        data = file.read()
        file.close()
        return data
    def _read_rules_file(self) -> str:
        """
        Function reads and returns welcome and rules message stored in rules.md
        :return:
        """
        file = open('messages/rules.md', mode='r')
        data = file.read()
        file.close()
        return data


async def setup(bot):
    await bot.add_cog(UpdateCountryMessage(bot))
