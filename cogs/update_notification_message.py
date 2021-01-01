import discord
from discord.ext import commands

from helpers.config import ROLES_CHANNEL
from helpers.message import embed
from helpers.message import roles


class UpdateNotificationMessage(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='update_notification', hidden=True)
    @commands.has_any_role(*roles())
    async def update(self, ctx, *, message_id: int = None):
        """
        Function posts updated countries message
        :param ctx:
        :param message_id:
        :return:
        """
        channel = discord.utils.get(ctx.message.guild.channels, id=ROLES_CHANNEL)
        if channel:
            author = {
                'name': self.bot.user.name,
                'url': 'https://vatsim-scandinavia.org',
                'icon': self.bot.user.avatar_url,
            }
            if message_id is None:
                try:
                    await ctx.message.delete()
                    embd = self._read_embed__file()
                    text = self._read_message_file()
                    msg = embed(description=embd, author=author)
                    await channel.send(text, embed=msg)
                except Exception as e:
                    print(e)
            else:
                message = discord.utils.get(await channel.history(limit=100).flatten(), id=message_id)

                if message:
                    try:
                        await ctx.message.delete()
                        embd = self._read_embed__file()
                        text = self._read_message_file()
                        msg = embed(description=embd, author=author)
                        await message.edit(content=text, embed=msg)
                    except Exception as e:
                        print(e)

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


def setup(bot):
    bot.add_cog(UpdateNotificationMessage(bot))
