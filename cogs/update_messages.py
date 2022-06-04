import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option

from helpers.config import ROLES_CHANNEL, GUILD_ID, RULES_CHANNEL, DIVISION_URL, WELCOME_CHANNEL
from helpers.message import embed
from helpers.message import staff_roles


class UpdateCountryMessage(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    guild_ids = [GUILD_ID]
    

    @cog_ext.cog_slash(name="update", guild_ids=guild_ids, description="Function posts updated countries message.",
    options=[
        create_option(
            name="option",
            description="Select which message you want to update",
            option_type=3,
            required=True,
            choices=[
            create_choice(
            name="Countries",
            value="1"
            ),
            create_choice(
            name="Notifications",
            value="2"
            ),
            create_choice(
            name="Welcome",
            value="3"
            ),
            create_choice(
            name="Rules",
            value="4"
            )]
        ),
        create_option(
            name="message_id",
            description="Select the message id of the message you want to update",
            option_type=3,
            required=False,
        )
    ])
        
    @commands.has_any_role(*staff_roles())
    async def update(self, ctx, *, message_id: str = None, option: str):
        """
        Function posts updated countries message
        :param ctx:
        :param message_id:
        :return:
        """
        if option == "1":
            channel = discord.utils.get(ctx.guild.channels, id=ROLES_CHANNEL)
            if channel:
                author = {
                    'name': self.bot.user.name,
                    'url': 'https://vatsim-scandinavia.org',
                    'icon': self.bot.user.avatar_url,
                }
                if message_id is None:
                    try:
                        await ctx.send("Message is being generated", delete_after=5)
                        text = self._read_file()
                        msg = embed(description=text, author=author)
                        await channel.send(embed=msg)
                    except Exception as e:
                        print(e)
                else:
                    message_id = int(message_id)
                    message = discord.utils.get(await ctx.channel.history(limit=100).flatten(), id=message_id)
                    
                    if message:
                        try:
                            await ctx.send("Message is being generated", delete_after=5)
                            text = self._read_file()
                            msg = embed(description=text, author=author)
                            await message.edit(embed=msg)
                        except Exception as e:
                            print(e)
        
        elif option == "2":
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
                    'url': 'https://vatsim-scandinavia.org',
                    'icon': self.bot.user.avatar_url,
                }
                if message_id is None:
                    try:
                        await ctx.send("Message is being generated", delete_after=5)
                        embd = self._read_embed__file()
                        text = self._read_message_file()
                        msg = embed(description=embd, author=author)
                        await channel.send(text, embed=msg)
                    except Exception as e:
                        print(e)
                else:
                    message_id = int(message_id)
                    message = discord.utils.get(await channel.history(limit=100).flatten(), id=message_id)
        
                    if message:
                        try:
                            await ctx.send("Message is being generated", delete_after=5)
                            embd = self._read_embed__file()
                            text = self._read_message_file()
                            msg = embed(description=embd, author=author)
                            await message.edit(content=text, embed=msg)
                        except Exception as e:
                            print(e)
        elif option == "3":
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
                    message = discord.utils.get(await channel.history(limit=100).flatten(), id=message_id)
    
                    if message:
                        try:
                            await ctx.send("Message is being generated", delete_after=5)
                            text = self._read_welcome_file()
                            msg = embed(title='Welcome', description=text, author=author)
                            await message.edit(embed=msg)
                        except Exception as e:
                            print(e)
        elif option == "4":
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
                    message = discord.utils.get(await channel.history(limit=100).flatten(), id=message_id)
    
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


def setup(bot):
    bot.add_cog(UpdateCountryMessage(bot))
