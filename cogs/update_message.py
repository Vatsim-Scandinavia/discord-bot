import discord
from discord.ext import commands

from helpers.config import RULES_CHANNEL
from helpers.message import embed
from helpers.message import roles


class UpdateMessageCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='update_message')
    @commands.has_any_role(*roles())
    async def update(self, ctx, *, message_id: int = None):
        """
        Function posts updated welcome and rules message
        :param ctx:
        :param message_id:
        :return:
        """
        channel = discord.utils.get(ctx.message.guild.channels, id=RULES_CHANNEL)
        if channel:
            author = {
                'name': self.bot.user.name,
                'url': 'https://vatsim-scandinavia.org',
                'icon': self.bot.user.avatar_url,
            }
            if message_id is None:
                try:
                    await ctx.message.delete()
                    text = self._read_file()
                    msg = embed(title='Rules', description=text, author=author)
                    await channel.send(embed=msg)
                except Exception as e:
                    print(e)
            else:
                message = discord.utils.get(await channel.history(limit=100).flatten(), id=message_id)

                if message:
                    try:
                        await ctx.message.delete()
                        text = self._read_file()
                        msg = embed(title='Rules', description=text, author=author)
                        await message.edit(embed=msg)
                    except Exception as e:
                        print(e)

    def _read_file(self) -> str:
        """
        Function reads and returns welcome and rules message stored in welcome_rules.md
        :return:
        """
        file = open('welcome_rules.md', mode='r')
        data = file.read()
        file.close()
        return data


def setup(bot):
    bot.add_cog(UpdateMessageCog(bot))
