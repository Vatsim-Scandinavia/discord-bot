import os
from datetime import datetime, timedelta
from discord.ext import commands, tasks
import mysql.connector


class UpdateMessageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.update_messages.start()

    def cog_unload(self):
        self.update_messages.cancel()

    @tasks.loop(seconds=2)
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
            if last_update != last_update_time:
                self._update_modified_time(last_update, mydb)
                await self._send_update()
        else:
            self._save_last_modified_time(mydb, last_update)
            print(last_update)


    def _get_last_modified_time(self, cursor):
        cursor.execute("SELECT last_update_time from message_updates")
        time = cursor.fetchone()

        return time[0]

    def _save_last_modified_time(self, db, time):
        cursor = db.cursor()
        cursor.execute(f"INSERT INTO message_updates (last_update_time) VALUES ({time})")
        db.commit()

    async def _send_update(self):
        print(self._read_file())

    def _read_file(self) -> str:
        file = open('welcome_rules.md', mode='r')
        data = file.read()
        file.close()
        return data

    def _update_modified_time(self, time: str, db):
        cursor = db.cursor()
        cursor.execute(f"UPDATE message_updates SET last_update_time = {time}")
        db.commit()


def setup(bot):
    bot.add_cog(UpdateMessageCog(bot))
