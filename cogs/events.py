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
        'calendars': 2,  # Community calendar only!
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
        #self.post_events.start()
        
       
        



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


        return

        channel = self.bot.get_channel(EVENTS_CHANNEL)
        role = channel.guild.get_role(EVENTS_ROLE)
        mydb = db_connection()

        events = await self._fetch_sql_events(mydb)
        for event in events:
            if self._should_be_published(event):

                # Publish reminder of event starting soon
                msg = embed(title=event[self.NAME], url=event[self.URL], description=event[self.DESCRIPTION], image=event[self.IMG],
                            timestamp=event[self.START], footer=self.FOOTER)
                text = f'{role.mention}\n:clock2: **This event starts in two hours!**'
                try:
                    await channel.send(text, embed=msg)
                    await self._mark_as_published(event[self.ID], mydb)
                except Exception as e:
                    await channel.send(text, embed=msg)
                    await self._mark_as_published(event[self.ID], mydb)










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


        # Refresh our current models
        mydb = db_connection()
        cursor = mydb.cursor()

        # Iterate over a copy of dict, so we can pop the original one
        for event in self.events.copy().values():
            success = await event.fetch_api_updates()

            # If not found in API, delete it from local and database records
            if not success:
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




    async def save_data(self):
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





    async def _refresh_events(self, mydb):
        """
        Function gets all events from the API and stores them
        :return:
        """

        cursor = mydb.cursor()
        channel = self.bot.get_channel(EVENTS_CHANNEL)
        auth = aiohttp.BasicAuth(os.getenv('FORUM_API_TOKEN'), '')

        stored_events = await self._fetch_sql_events(mydb)
        
        # Fetch newest data from API
        async with aiohttp.ClientSession() as session:
            for stored_event in stored_events:
                # Check for updates of the already stored events
                async with session.get(self.RSS_FEED_URL + "/" + str(stored_event[self.EVENT_ID]), auth=auth) as resp:

                    # Update if found, delete if not
                    if resp.status == 200:
                        updated_event = await resp.json()

                        # Delete if it's soft deleted aka. hidden
                        if updated_event.get('hidden'):
                            ID = updated_event.get('id')
                            cursor.execute(f'DELETE FROM events WHERE event_id = {ID}')

                        cursor.execute(
                            "UPDATE events SET name = %s, url = %s, img = %s, description = %s, start_time = %s, recurring = %s, recurring_interval = %s, recurring_end = %s WHERE event_id = '%s'",
                            (updated_event.get('title'), updated_event.get('url'), get_image(updated_event.get('description')),
                            event_description(updated_event.get('description')), self._convert_time(updated_event.get('start')),
                            self._get_ics_freq(updated_event.get('recurrence')), self._get_ics_interval(updated_event.get('recurrence')), self._get_ics_recurring_end(updated_event.get('recurrence'), updated_event.get('start')),
                            updated_event.get('id')))
                    elif resp.status == 404:
                        ID = stored_event[self.EVENT_ID]
                        cursor.execute(f'DELETE FROM events WHERE event_id = {ID}')
                    
            # Grab all NEW event data from API
            async with session.get(self.RSS_FEED_URL, auth=auth, params=self.PARAMS) as resp2:
                assert resp2.status == 200
                new_events = await resp2.json()
        
        # Process and store them and exclude already existing events
        for new_event in new_events['results']:
            
            # Skip already expired events
            if self._convert_time(new_event.get('start')) < datetime.utcnow():
                continue

            # Skip already stored and updated events
            found_event = False
            for stored_event in stored_events: 
                if new_event.get('id') == stored_event[self.EVENT_ID]:
                    found_event = True
                    break

            if found_event:
                continue


            # Insert the new event to the database
            # In the edge case of updating a existing but expired event, fallback on DUPLICATE KEY is made
            cursor.execute(
                    "INSERT INTO events (name, url, img, description, start_time, recurring, recurring_interval, recurring_end, event_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE name = VALUES(name), url = VALUES(url), img = VALUES(img), description = VALUES(description), start_time = VALUES(start_time), recurring = VALUES(recurring), recurring_interval = VALUES(recurring_interval), recurring_end = VALUES(recurring_end)",
                    (new_event.get('title'), new_event.get('url'), get_image(new_event.get('description')),
                     event_description(new_event.get('description')), self._convert_time(new_event.get('start')),
                     self._get_ics_freq(new_event.get('recurrence')), self._get_ics_interval(new_event.get('recurrence')), self._get_ics_recurring_end(new_event.get('recurrence'), new_event.get('start')),
                     new_event.get('id')))

            #Publish the newly scheduled event in channel
            msg = embed(title=new_event.get('title'), url=new_event.get('url'), description=event_description(new_event.get('description')),
                        image=get_image(new_event.get('description')),
                        timestamp=self._convert_time(new_event.get('start')), footer=self.FOOTER)
            await channel.send(embed=msg)

        mydb.commit()


    async def _fetch_sql_events(self, mydb) -> list:
        """
        Function fetches events stored in database
        :param mydb:
        :return:
        """
        cursor = mydb.cursor()

        # Get unpublished events or recurring events that has been published as potential events
        cursor.execute("SELECT * FROM events WHERE published IS NULL OR (published IS NOT NULL AND recurring IS NULL AND UTC_TIMESTAMP() <= start_time) OR (published IS NOT NULL AND recurring IS NOT NULL AND UTC_TIMESTAMP() <= recurring_end)")

        return cursor.fetchall()


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










    #
    # ----------------------------------
    #   OTHER FUNCTIONS
    # ----------------------------------
    #

    def _should_be_published(self, event):
        """
        Function checks should event be posted
        :param event:
        :return:
        """

        start = event[self.START]
        now = datetime.utcnow()

        recurring = event[self.RECURRING]
        recurring_end = event[self.RECURRING_END]
        interval = event[self.RECURRING_INTERVAL]
        published = event[self.PUBLISHED]

        # Check if it's a recurring event
        if recurring and recurring_end >= now:
            recurred_date = self._get_recurred_date(start, interval, recurring, recurring_end)

            # If today is notification day and we've not already notified
            if recurred_date is not False:
                # Go on if it's never been published
                if published is None:
                    start = recurred_date
                # Go on if it's not passed two hours since last publish
                elif datetime.utcnow() > published + timedelta(hours = 2):
                    start = recurred_date
                else:
                    return False
            else:
                return False

        # Define the when it's 2 hours prior, and the threshold of notifying to avoid notifications way too late
        notificationTime = start - timedelta(hours=2)
        notificationThreshold = start - timedelta(hours=1.75)

        return (now >= notificationTime and now <= notificationThreshold)

    def _convert_time(self, time: str) -> datetime:
        """
        Function converts time to SQL time
        :param time:
        :return:
        """
        return datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")

    def _split_ics_params(self, ics: str):
        params = {}
        for param in ics.split(';'):
            split = param.split('=')
            params[split[0].lower()] = split[1]

        return params

    def _get_ics_recurring_end(self, ics: str, start_time: str):
        """
        Function to parse ICS calendar recurring format into the end date of event
        :param ics:
        :return:
        """

        # Return null if there's no recurring
        if ics is None:
            return None

        # Split the ICS parameters into a table
        params = self._split_ics_params(ics)

        # If until timestamp has been selected, let's use that
        if "until" in params:
            return datetime.strptime(params["until"], "%Y%m%dT%H%M%S")

        # If no timestamp has been given, calculate based on the interval
        if "count" in params:
            if params["freq"] == "DAILY":
                return datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ") + timedelta(days = (int(params["count"]) * int(params["interval"]) ))
            elif params["freq"] == "WEEKLY":
                return datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ") + timedelta(weeks = (int(params["count"]) * int(params["interval"]) ))
            elif params["freq"] == "MONTHLY":
                return datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ") + timedelta(months = (int(params["count"]) * int(params["interval"]) ))

        # If no timestamp selected, none can be calculated, then this is probably an event without end date
        return datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ") + timedelta(days=(365*10))

    def _get_ics_freq(self, ics: str):
        """
        Function fetches the frequency of recurrence
        :param ics:
        :return:
        """

        # Return null if there's no recurring
        if ics is None:
            return None

        # Split the ICS parameters into a table
        params = self._split_ics_params(ics)

        if "freq" in params:
            return params["freq"]
        else:
            return None 

    def _get_ics_interval(self, ics: str):
        """
        Function fetches the interval of recurrence
        :param ics:
        :return:
        """

        # Return null if there's no recurring
        if ics is None:
            return None

        # Split the ICS parameters into a table
        params = self._split_ics_params(ics)

        if "interval" in params:
            if params["interval"] is not None:
                return params["interval"]

        return None 

    def _get_recurred_date(self, proposed_date, interval, recurring, recurring_end):
        """
        Function which returns a list of possible dates
        :param event:
        :return:
        """

        interval = interval or 1

        while(proposed_date <= recurring_end):

                # Break if we're past today
                if proposed_date.date() > datetime.utcnow().date():
                    break

                # Does the day isolated match today?
                if proposed_date.date() == datetime.utcnow().date():
                    return proposed_date

                if recurring == "DAILY":
                    proposed_date = proposed_date + timedelta(days=interval)
                elif recurring == "WEEKLY":
                    proposed_date = proposed_date + timedelta(weeks=interval)
                elif recurring == "MONTHLY":
                    proposed_date = proposed_date + timedelta(months=interval)
                else:
                    return False
        
        return False
          

def setup(bot):
    bot.add_cog(EventsCog(bot))