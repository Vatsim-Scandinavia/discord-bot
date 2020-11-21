from discord.ext import commands, tasks
from xml.dom import minidom
import aiohttp
from helpers.config import POST_EVENTS_INTERVAL, EVENTS_CHANNEL
import os
from datetime import datetime
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
        events = await self._get_events()

        for event in events['results']:
            author = {
                'name': self.bot.user.name,
                'url': event['url'],
                'icon': self.bot.user.avatar_url,
            }
            msg = embed(author=author, title=event['title'], description=event_description(event['description']), image=get_image(event['description']))
            await self.bot.get_channel(EVENTS_CHANNEL).send(embed=msg)

    async def _get_events(self) -> str:
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(os.getenv('API_TOKEN'), '')
            async with session.get(self.RSS_FEED_URL, auth=auth, params=self.PARAMS) as resp:
                return await resp.json()


def setup(bot):
    bot.add_cog(EventsCog(bot))
