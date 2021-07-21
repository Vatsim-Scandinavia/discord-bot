import os
from datetime import datetime, timedelta
from discord_slash import cog_ext

import aiohttp
import mysql.connector
from discord.ext import commands, tasks

from helpers.config import POST_EVENTS_INTERVAL, EVENTS_CHANNEL, EVENTS_ROLE, GUILD_ID
from helpers.message import embed, event_description, get_image

guild_ids = [GUILD_ID]

class EventsCog(commands.Cog):
    RSS_FEED_URL = 'https://vatsim-scandinavia.org/api/calendar/events'
    PARAMS = {
        'rangeStart': datetime.now().strftime('%Y-%m-%d'),
        'perPage': 25,
        'hidden': 0,
        'calendars': 1,  # Community calendar only!
    }

    ID = 0
    NAME = 1
    IMG = 2
    URL = 3
    DESCRIPTION = 4
    START = 5

    FOOTER = {
        'text': 'Starting time',
        'icon': 'https://twemoji.maxcdn.com/v/latest/72x72/1f551.png',
    }


    def __init__(self, bot):
        self.bot = bot
        self.events.start()


    def cog_unload(self):
        self.events.cancel()



    @tasks.loop(seconds=POST_EVENTS_INTERVAL)
    async def events(self):
        """
        Task looks up all events and posts ones that take place in next 1 and a half hour
        :return:
        """
        await self.bot.wait_until_ready()

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
                msg = embed(title=event[self.NAME], url=event[self.URL], description=event[self.DESCRIPTION], image=event[self.IMG],
                            timestamp=event[self.START], footer=self.FOOTER)
                text = f'{role.mention}\n:clock2: **This event starts in two hours!**'
                try:
                    await channel.send(text, embed=msg)
                    await self._mark_as_published(event[self.ID], mydb)
                except Exception as e:
                    await channel.send(text, embed=msg)
                    await self._mark_as_published(event[self.ID], mydb)

    async def _get_events(self) -> str:
        """
        Function gets all events from the API
        :return:
        """
        
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(os.getenv('FORUM_API_TOKEN'), '')
            async with session.get(self.RSS_FEED_URL, auth=auth, params=self.PARAMS) as resp:
                return await resp.json()

    async def _save_events(self, events, mydb):
        """
        Function stores events that weren't saved already
        :param events:
        :param mydb:
        :return:
        """
        cursor = mydb.cursor()
        channel = self.bot.get_channel(EVENTS_CHANNEL)
        for event in events['results']:
            if self._convert_time(event.get('start')) < datetime.utcnow():
                continue

            cursor.execute(f"SELECT * FROM events WHERE event_id = {event.get('id')}")

            result = cursor.fetchone()

            if result != None:
                cursor.execute(
                    "UPDATE events SET name = %s, url = %s, img = %s, description = %s, start_time = %s, recurring = %s WHERE event_id = '%s'",
                    (event.get('title'), event.get('url'), get_image(event.get('description')),
                     event_description(event.get('description')), self._convert_time(event.get('start')), event.get('recurrence'),
                     event.get('id')))
            else:
                cursor.execute(
                    "INSERT INTO events (name, url, img, description, start_time, recurring, event_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (event.get('title'), event.get('url'), get_image(event.get('description')),
                     event_description(event.get('description')), self._convert_time(event.get('start')), event.get('recurrence'),
                     event.get('id')))
                msg = embed(title=event.get('title'), url=event.get('url'), description=event_description(event.get('description')),
                            image=get_image(event.get('description')),
                            timestamp=self._convert_time(event.get('start')), footer=self.FOOTER)
                await channel.send(embed=msg)
        mydb.commit()

    def _convert_time(self, time: str) -> datetime:
        """
        Function converts time to SQL time
        :param time:
        :return:
        """
        return datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")

    async def _fetch_events(self, mydb) -> list:
        """
        Function fetches events stored in database
        :param mydb:
        :return:
        """
        cursor = mydb.cursor()

        cursor.execute("SELECT * FROM events WHERE published IS NULL")
        # TODO Add recurring events support

        return cursor.fetchall()

    def _should_be_published(self, start: datetime):
        """
        Function checks should event be posted
        :param start:
        :return:
        """

        # Define the when it's 2 hours prior, and the threshold of notifying to avoid notifications way too late
        notificationTime = start - timedelta(hours=2)
        notificationThreshold = start - timedelta(hours=1.75)
        now = datetime.utcnow()

        return (now >= notificationTime and now <= notificationThreshold)

    async def _mark_as_published(self, ID: int, mydb):
        """
        Function updates events and sets it as published in the database
        :param ID:
        :param mydb:
        :return:
        """
        cursor = mydb.cursor()

        cursor.execute(f'UPDATE events SET published = UTC_TIMESTAMP() WHERE id = {ID}')

        mydb.commit()
                
def setup(bot):
    bot.add_cog(EventsCog(bot))