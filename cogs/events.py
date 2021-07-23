import os
from datetime import datetime, timedelta
from discord_slash import cog_ext

import aiohttp
from discord.ext import commands, tasks

from helpers.config import POST_EVENTS_INTERVAL, GET_EVENTS_INTERVAL, EVENTS_CHANNEL, EVENTS_ROLE, GUILD_ID
from helpers.message import embed, event_description, get_image
from helpers.database import db_connection
from helpers.event import Event

guild_ids = [GUILD_ID]

class EventsCog(commands.Cog):

    #
    # ----------------------------------
    #   CONSTANTS
    # ----------------------------------
    #

    # API Configurations
    RSS_FEED_URL = 'https://vatsim-scandinavia.org/api/calendar/events'
    PARAMS = {
        'perPage': 25,
        'hidden': 0,
        'sortDir': 'desc',
        'calendars': 1,  # Community calendar only!
    }

    # Indexing of database return
    DB_ID = 0
    DB_NAME = 1
    DB_IMG = 2
    DB_URL = 3
    DB_DESCRIPTION = 4
    DB_START = 5
    DB_RECURRING = 6
    DB_RECURRING_INTERVAL = 7
    DB_RECURRING_END = 8
    DB_PUBLISHED = 9

    # Embed parameters
    FOOTER = {
        'text': 'Starting time',
        'icon': 'https://twemoji.maxcdn.com/v/latest/72x72/1f551.png',
    }








    #
    # ----------------------------------
    #   COG FUNCTIONS
    # ----------------------------------
    #

    def __init__(self, bot):
        self.bot = bot
        self.events = {}

        self.get_events.start()
        self.post_events.start()
        
       
        



    def cog_unload(self):
        self.get_events.cancel()
        self.post_events.cancel()








    #
    # ----------------------------------
    #   LOOPING TASKS
    # ----------------------------------
    #

    @tasks.loop(seconds=GET_EVENTS_INTERVAL)
    async def get_events(self):
        """
        Task to fetch and refresh events from API
        """

        await self.bot.wait_until_ready()

        # Load all data if none is filled
        if len(self.events) == 0:
            await self.load_data()

        # Get fresh data from API
        await self.fetch_api()

        # Save data countinously
        await self.save_data()


    @tasks.loop(seconds=POST_EVENTS_INTERVAL)
    async def post_events(self):
        """
        Task to post event reminders
        :return:
        """

        await self.bot.wait_until_ready()

        channel = self.bot.get_channel(EVENTS_CHANNEL)
        role = channel.guild.get_role(EVENTS_ROLE)

        for event in self.events.values():
            
            # If event object says it should be notified and it's not a old and expired event
            if event.should_be_notified() and not event.is_expired():

                msg = embed(
                    title=event.name, 
                    url=event.url, 
                    description=event.desc,
                    image=event.img,
                    timestamp=event.start, 
                    footer=self.FOOTER
                )

                text = f'{role.mention}\n:clock2: **This event starts in two hours!**'
                await channel.send(text, embed=msg)

                event.mark_as_published()
                









    #
    # ----------------------------------
    #   ASYNC DATA FUNCTIONS
    # ----------------------------------
    #

    async def load_data(self):
        """
        Build the classes based on what's already stored in the database
        """

        mydb = db_connection()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM events")

        db_events = cursor.fetchall()

        for db_event in db_events:
            self.events[db_event[self.DB_ID]] = Event(
                db_event[self.DB_ID],
                db_event[self.DB_NAME],
                db_event[self.DB_IMG],
                db_event[self.DB_URL],
                db_event[self.DB_DESCRIPTION],
                db_event[self.DB_START],
                db_event[self.DB_RECURRING],
                db_event[self.DB_RECURRING_INTERVAL],
                db_event[self.DB_RECURRING_END],
                db_event[self.DB_PUBLISHED],
            )




    async def fetch_api(self):
        """
        Fetch fresh updates for our existing events and create new ones
        """

        # Refresh our current models
        mydb = db_connection()
        cursor = mydb.cursor()

        # Iterate over a copy of dict, so we can pop the original one
        for event in self.events.copy().values():
            success = await event.fetch_api_updates()

            # If not found in API, delete it from local and database records
            if not success or event.is_expired():
                ID = event.id
                self.events.pop(ID)
                cursor.execute(f'DELETE FROM events WHERE id = {ID}')

        mydb.commit()




        # Refresh potential new models
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(os.getenv('FORUM_API_TOKEN'), '')
            async with session.get(self.RSS_FEED_URL, auth=auth, params=self.PARAMS) as resp:
                assert resp.status == 200
                new_events = await resp.json()

        for new_event in new_events['results']:
            # Skip already expired events
            if self._convert_time(new_event.get('start')) < datetime.utcnow():
                continue

            # Skip already stored and updated events
            found_event = False
            for stored_event in self.events.values(): 
                if new_event.get('id') == stored_event.id:
                    found_event = True
                    break

            if found_event:
                continue
            
            # Create the object
            self.events[new_event.get('id')] = Event(
                new_event.get('id'),
                new_event.get('title'),
                get_image(new_event.get('description')),
                new_event.get('url'),
                event_description(new_event.get('description')),
                self._convert_time(new_event.get('start')),
                None,
                None,
                None,
                None
            )

            # Parse the recurrence data if any
            if new_event.get('recurrence') is not None:
                self.events[new_event.get('id')].parse_recurrence(new_event.get('recurrence'))


            # Publish the newly scheduled event in channel
            channel = self.bot.get_channel(EVENTS_CHANNEL)
            e = self.events[new_event.get('id')]
            msg = embed(
                title=e.name, 
                url=e.url, 
                description=e.desc,
                image=e.img,
                timestamp=e.start, 
                footer=self.FOOTER
            )
            await channel.send(embed=msg)





    async def save_data(self):
        """
        Save all data so far to MySQL
        """

        for event in self.events.values():

            mydb = db_connection()
            cursor = mydb.cursor()
            cursor.execute(
                "INSERT INTO events (id, name, img, url, description, start_time, recurring, recurring_interval, recurring_end, published) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE name = VALUES(name), img = VALUES(img), url = VALUES(url), description = VALUES(description), start_time = VALUES(start_time), recurring = VALUES(recurring), recurring_interval = VALUES(recurring_interval), recurring_end = VALUES(recurring_end), published = VALUES(published)",
                (
                    event.id,
                    event.name,
                    event.img,
                    event.url,
                    event.desc,
                    
                    event.start,
                    event.recurring,
                    event.recurring_interval,
                    event.recurring_end,

                    event.published,
                )
            )

            mydb.commit()










    #
    # ----------------------------------
    #   OTHER FUNCTIONS
    # ----------------------------------
    #

    def _convert_time(self, time: str) -> datetime:
        """
        Function converts time to SQL time
        """
        return datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
          

def setup(bot):
    bot.add_cog(EventsCog(bot))