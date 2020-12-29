import os
from datetime import datetime, timedelta
from discord.ext import commands, tasks
import mysql.connector
from helpers.message import embed
from helpers.config import RULES_CHANNEL, CHECK_RULES_INTERVAL


class UpdateMessageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.update_messages.start()

    def cog_unload(self):
        self.update_messages.cancel()

    @tasks.loop(seconds=CHECK_RULES_INTERVAL)
    async def update_messages(self):
        mydb = mysql.connector.connect(
            host="localhost",
            user=os.getenv('BOT_DB_USER'),
            password=os.getenv('BOT_DB_PASSWORD'),
            database=os.getenv('BOT_DB_NAME')
        )
        cursor = mydb.cursor()
        last_update_time = self._get_last_modified_time(cursor)
        last_update = os.stat('welcome_rules.md').st_mtime

        if last_update_time:
            last_update = str(last_update)
            if last_update != last_update_time[0]:
                try:
                    self._update_modified_time(last_update, mydb)
                    await self._delete_messages()
                    await self._send_update()
                except Exception as e:
                    print(e)
        else:
            try:
                self._save_last_modified_time(mydb, last_update)
                await self._delete_messages()
                await self._send_update()
            except Exception as e:
                print(e)


    def _get_last_modified_time(self, cursor):
        cursor.execute("SELECT last_update_time from message_updates")
        time = cursor.fetchone()

        return time

    def _save_last_modified_time(self, db, time):
        cursor = db.cursor()
        cursor.execute(f"INSERT INTO message_updates (last_update_time) VALUES ({time})")
        db.commit()

    async def _send_update(self):
        author = {
            'name': self.bot.user.name,
            'url': 'https://vatsim-scandinavia.org',
            'icon': self.bot.user.avatar_url,
        }
        channel = self.bot.get_channel(RULES_CHANNEL)
        text = self._read_file()
        msg = embed(title='Rules', description=text, author=author)
        await channel.send(embed=msg)

    def _read_file(self) -> str:
        file = open('welcome_rules.md', mode='r')
        data = file.read()
        file.close()
        return data

    def _update_modified_time(self, time: str, db):
        cursor = db.cursor()
        cursor.execute(f"UPDATE message_updates SET last_update_time = {time}")
        db.commit()

    async def _delete_messages(self):
        msg_delete = []
        channel = self.bot.get_channel(RULES_CHANNEL)
        async for msg in channel.history(limit=100):
            msg_delete.append(msg)

        await channel.delete_messages(msg_delete)


def setup(bot):
    bot.add_cog(UpdateMessageCog(bot))
