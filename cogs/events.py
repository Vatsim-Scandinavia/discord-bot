import os
from datetime import datetime
import mysql.connector
from datetime import datetime

import aiohttp
from discord.ext import commands, tasks

from helpers.config import POST_EVENTS_INTERVAL, EVENTS_CHANNEL
from helpers.message import embed, event_description, get_image


class EventsCog(commands.Cog):
    RSS_FEED_URL = 'https://vatsim-scandinavia.org/api/calendar/events'
    PARAMS = {
        'rangeStart': datetime.now().strftime('%Y-%m-%d'),
        'perPage': 50,
        'hidden': 0,
        'calendars': 1,  # Community calendar only!
    }

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.events.start()

    def cog_unload(self):
        self.events.cancel()

    @tasks.loop(seconds=POST_EVENTS_INTERVAL)
    async def events(self):
        mydb = mysql.connector.connect(
            host="localhost",
            user=os.getenv('BOT_DB_USER'),
            password=os.getenv('BOT_DB_PASSWORD'),
            database=os.getenv('BOT_DB_NAME')
        )

        events = await self._get_events()
        await self._save_events(events, mydb)

        """for event in events['results']:
            author = {
                'name': self.bot.user.name,
                'url': event['url'],
                'icon': self.bot.user.avatar_url,
            }
            msg = embed(author=author, title=event['title'], description=, image=)
            await self.bot.get_channel(EVENTS_CHANNEL).send(embed=msg)"""

    async def _get_events(self) -> str:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(os.getenv('API_TOKEN'), '')
            async with session.get(self.RSS_FEED_URL, auth=auth, params=self.PARAMS) as resp:
                return await resp.json()

    async def _save_events(self, events, mydb):
        cursor = mydb.cursor()
        for event in events['results']:
            cursor.execute(f"SELECT * FROM events WHERE event_id = {event.get('id')}")

            result = cursor.fetchone()

            if result != None:
                cursor.execute("UPDATE events SET name = %s, url = %s, img = %s, description = %s, start_time = %s WHERE event_id = '%s'",
                               (event.get('title'), event.get('url'), get_image(event.get('description')),
                               event_description(event.get('description')), self._convert_time(event.get('start')),
                               event.get('id')))
            else:
                cursor.execute("INSERT INTO events (name, url, img, description, start_time, event_id) VALUES (%s, %s, %s, %s, %s, %s)",
                               (event.get('title'), event.get('url'), get_image(event.get('description')),
                               event_description(event.get('description')), self._convert_time(event.get('start')), event.get('id')))
        mydb.commit()

    def _convert_time(self, time: str) -> datetime:
        return datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")


def setup(bot):
    bot.add_cog(EventsCog(bot))
