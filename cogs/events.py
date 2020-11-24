import os
from datetime import datetime, timedelta

import aiohttp
import mysql.connector
from discord.ext import commands, tasks

from helpers.config import POST_EVENTS_INTERVAL, EVENTS_CHANNEL, EVENTS_ROLE
from helpers.message import embed, event_description, get_image


class EventsCog(commands.Cog):
    RSS_FEED_URL = 'https://vatsim-scandinavia.org/api/calendar/events'
    PARAMS = {
        'rangeStart': datetime.now().strftime('%Y-%m-%d'),
        'perPage': 50,
        'hidden': 0,
        'calendars': 1,  # Community calendar only!
    }

    ID = 0
    NAME = 1
    IMG = 2
    URL = 3
    DESCRIPTION = 4
    START = 5

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.events.start()

    def cog_unload(self):
        self.events.cancel()

    @tasks.loop(seconds=POST_EVENTS_INTERVAL)
    async def events(self):
        channel = self.bot.get_channel(EVENTS_CHANNEL)
        role = channel.guild.get_role(EVENTS_ROLE)
        mydb = mysql.connector.connect(
            host="localhost",
            user=os.getenv('BOT_DB_USER'),
            password=os.getenv('BOT_DB_PASSWORD'),
            database=os.getenv('BOT_DB_NAME')
        )

        events = await self._get_events()
        await self._save_events(events, mydb)

        events = await self._fetch_events(mydb)

        for event in events:
            if self._should_be_published(event[self.START]):
                msg = embed(title=event[self.NAME], description=event[self.DESCRIPTION], image=event[self.IMG])
                try:
                    await channel.send(role.mention, embed=msg)
                    await self._mark_as_published(event[self.ID], mydb)
                except Exception as e:
                    await channel.send(role.mention, embed=msg)
                    await self._mark_as_published(event[self.ID], mydb)

    async def _get_events(self) -> str:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(os.getenv('API_TOKEN'), '')
            async with session.get(self.RSS_FEED_URL, auth=auth, params=self.PARAMS) as resp:
                return await resp.json()

    async def _save_events(self, events, mydb):
        cursor = mydb.cursor()
        for event in events['results']:
            if self._convert_time(event.get('start')) < datetime.utcnow():
                continue

            cursor.execute(f"SELECT * FROM events WHERE event_id = {event.get('id')}")

            result = cursor.fetchone()

            if result != None:
                cursor.execute(
                    "UPDATE events SET name = %s, url = %s, img = %s, description = %s, start_time = %s WHERE event_id = '%s'",
                    (event.get('title'), event.get('url'), get_image(event.get('description')),
                     event_description(event.get('description')), self._convert_time(event.get('start')),
                     event.get('id')))
            else:
                cursor.execute(
                    "INSERT INTO events (name, url, img, description, start_time, event_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    (event.get('title'), event.get('url'), get_image(event.get('description')),
                     event_description(event.get('description')), self._convert_time(event.get('start')),
                     event.get('id')))
        mydb.commit()

    def _convert_time(self, time: str) -> datetime:
        return datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")

    async def _fetch_events(self, mydb) -> list:
        cursor = mydb.cursor()

        cursor.execute("SELECT * FROM events WHERE published = FALSE")

        return cursor.fetchall()

    def _should_be_published(self, start: datetime):
        return start - timedelta(hours=1, minutes=30) <= datetime.utcnow()

    async def _mark_as_published(self, ID: int, mydb):
        cursor = mydb.cursor()

        cursor.execute(f'UPDATE events SET published = TRUE WHERE id = {ID}')

        mydb.commit()


def setup(bot):
    bot.add_cog(EventsCog(bot))
