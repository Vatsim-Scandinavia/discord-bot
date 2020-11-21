from discord.ext import commands, tasks
from xml.dom import minidom
import aiohttp
from helpers.config import POST_EVENTS_INTERVAL


class EventsCog(commands.Cog):
    RSS_FEED_URL = 'https://vatsim-scandinavia.org/rss/1-vatsca-events.xml'

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
        parsed_events = self._parse_xml(events)

        for event in parsed_events:
            print(event.description)

    async def _get_events(self) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.RSS_FEED_URL) as resp:
                return await resp.text()

    def _parse_xml(self, xml: str) -> list:
        try:
            data = minidom.parseString(xml)

            return data.getElementsByTagName('item')
        except Exception as e:
            print(e)
            return []


def setup(bot):
    bot.add_cog(EventsCog(bot))
