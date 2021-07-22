import os
from datetime import datetime, timedelta
from discord_slash import cog_ext

import aiohttp
import mysql.connector
from discord.ext import commands, tasks

from helpers.config import POST_EVENTS_INTERVAL, GET_EVENTS_INTERVAL, EVENTS_CHANNEL, EVENTS_ROLE, GUILD_ID
from helpers.message import embed, event_description, get_image

guild_ids = [GUILD_ID]

class EventsCog(commands.Cog):

    # API Configurations
    RSS_FEED_URL = 'https://vatsim-scandinavia.org/api/calendar/events'
    PARAMS = {
        'perPage': 25,
        'hidden': 0,
        'sortDir': 'desc',
        'calendars': 2,  # Community calendar only!
    }

    # Indexing of database return
    ID = 0
    NAME = 1
    IMG = 2
    URL = 3
    DESCRIPTION = 4
    START = 5
    RECURRING = 6
    RECURRING_INTERVAL = 7
    RECURRING_END = 8
    PUBLISHED = 9
    EVENT_ID = 10

    # Embed parameters
    FOOTER = {
        'text': 'Starting time',
        'icon': 'https://twemoji.maxcdn.com/v/latest/72x72/1f551.png',
    }






    #
    # Cog Functions
    #

    def __init__(self, bot):
        self.bot = bot
        self.fetch.start()
        self.events.start()


    def cog_unload(self):
        self.fetch.cancel()
        self.events.cancel()







    #
    # Tasks
    #

    @tasks.loop(seconds=GET_EVENTS_INTERVAL)
    async def fetch(self):
        """
        Task to fetch and refresh events from API
        :return:
        """
        await self.bot.wait_until_ready()

        mydb = mysql.connector.connect(
            host="localhost",
            user=os.getenv('BOT_DB_USER'),
            password=os.getenv('BOT_DB_PASSWORD'),
            database=os.getenv('BOT_DB_NAME')
        )

        # Fetch and store events
        await self._refresh_events(mydb)

        mydb.close()



    @tasks.loop(seconds=POST_EVENTS_INTERVAL)
    async def events(self):
        """
        Task to post event reminders
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

        mydb.close()






    #
    # ASYNC Functions
    #

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
                    continue

            if found_event:
                continue


            # Insert the new event to the database
            cursor.execute(
                    "INSERT INTO events (name, url, img, description, start_time, recurring, recurring_interval, recurring_end, event_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (new_event.get('title'), new_event.get('url'), get_image(new_event.get('description')),
                     event_description(new_event.get('description')), self._convert_time(new_event.get('start')),
                     self._get_ics_freq(new_event.get('recurrence')), self._get_ics_interval(updated_event.get('recurrence')), self._get_ics_recurring_end(new_event.get('recurrence'), new_event.get('start')),
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
        cursor.execute("SELECT * FROM events WHERE published IS NULL OR (published IS NOT NULL AND recurring IS NOT NULL AND UTC_TIMESTAMP() <= recurring_end)")

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
    # OTHER Functions
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

        # Check if it's a recurring event
        if recurring and recurring_end >= now:
            recurred_date = self._get_today_is_recurred_date(start, interval, recurring, recurring_end)

            if recurred_date:
                start = recurred_date
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
            return params["interval"]
        else:
            return None 

    def _get_today_is_recurred_date(self, start, interval, recurring, recurring_end):
        """
        Function which returns a list of possible dates
        :param event:
        :return:
        """

        proposed_date = start

        while(proposed_date <= recurring_end):
                if recurring == "DAILY":
                    proposed_date = proposed_date + timedelta(days=interval)
                elif recurring == "WEEKLY":
                    proposed_date = proposed_date + timedelta(weeks=interval)
                elif recurring == "MONTHLY":
                    proposed_date = proposed_date + timedelta(months=interval)
                else:
                    return False

                # Does the day isolated match today?
                if proposed_date == datetime.today():
                    return proposed_date
        
        return False
          

def setup(bot):
    bot.add_cog(EventsCog(bot))