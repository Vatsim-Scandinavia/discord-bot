import aiohttp

from datetime import datetime

from discord.ext import commands, tasks

from helpers.config import EVENT_CALENDAR_URL, EVENT_CALENDAR_TYPE, EVENT_API_TOKEN, GET_EVENTS_INTERVAL, POST_EVENTS_INTERVAL, DELETE_EVENTS_INTERVAL, EVENTS_CHANNEL, EVENTS_ROLE, DEBUG
from helpers.message import embed, event_description, get_image
from helpers.database import db_connection
from helpers.event import Event

class EventsCog(commands.Cog):
    #
    # ----------------------------------
    #   CONSTANTS
    # ----------------------------------
    #

    # API Configurations
    RSS_FEED_URL = EVENT_CALENDAR_URL + f'/calendars/{EVENT_CALENDAR_TYPE}/events'


    DB_ID = 0
    DB_NAME = 1
    DB_IMG = 2
    DB_URL = 3
    DB_DESCRIPTION = 4
    DB_START = 5
    DB_END = 6
    DB_PUBLISHED = 10

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
        self.delete_event_messages.start()

    def cog_unload(self):
        self.get_events.cancel()
        self.post_events.cancel()
        self.delete_event_messages.cancel()


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
                
                # Set the correct event start time to embed if its recurring
                start_time = event.start
                msg = embed(
                    title=event.name,
                    url=event.url,
                    description=event.desc,
                    image=event.img,
                    timestamp=start_time,
                    footer=self.FOOTER
                )

                text = f'{role.mention}\n:clock2: **{event.name}** is starting in two hours!'
                message = await channel.send(text, embed=msg)

                if DEBUG == False: await message.publish()

                event.mark_as_published()
                await self.store_message_expire(message, event._get_expire_datetime())

        
    @tasks.loop(seconds=DELETE_EVENTS_INTERVAL)
    async def delete_event_messages(self):
        mydb = db_connection()
        cursor = mydb.cursor()

        cursor.execute(f"SELECT * FROM event_messages")
        event_details = cursor.fetchall()

        channel = self.bot.get_channel(int(EVENTS_CHANNEL))


        now = datetime.utcnow()
        for event in event_details:
            if now > event[1]:
                try:
                    message = await channel.fetch_message(int(event[0]))
                    await message.delete()
                    cursor.execute(f"DELETE FROM event_messages WHERE message_id = {message.id}")

                except:
                    print("Did not find message id " + str(event[0]) + ". Deleting from database.", flush=True)
                    cursor.execute(f"DELETE FROM event_messages WHERE message_id = {int(event[0])}")
                    return


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
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT * FROM events')

        db_events = cursor.fetchall()

        for db_event in db_events:
            self.events[db_event[self.DB_ID]] = Event(
                db_event[self.DB_ID],
                db_event[self.DB_NAME],
                db_event[self.DB_IMG],
                db_event[self.DB_URL],
                db_event[self.DB_DESCRIPTION],
                db_event[self.DB_START],
                db_event[self.DB_END],
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
            headers =  {
                'accept': 'application/json',
                'Authorization': f"Bearer {EVENT_API_TOKEN}"
            }
            async with session.get(url=self.RSS_FEED_URL, headers=headers) as resp:
                assert resp.status == 200
                new_events = await resp.json()
            
            for new_event in new_events['data']:
                # Skip already expired events
                if self._convert_time(new_event.get('start_date')) < datetime.utcnow():
                    continue
                
                # Skip already stored and updated events
                found_event = False
                for stored_event in self.events.values():
                    if new_event.get('id') == stored_event.id:
                        found_event = True
                        break
                
                if found_event:
                    continue

                if new_event.get('start_date') is None or new_event.get('end_date') is None:
                    continue

                # Create the object
                self.events[new_event.get('id')] = Event(
                    new_event.get('id'),
                    new_event.get('title'),
                    new_event.get('image'),
                    new_event.get('link'),
                    event_description(new_event.get('long_description')),
                    self._convert_time(new_event.get('start_date')),
                    self._convert_time(new_event.get('end_date')),
                    None
                )

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

                text = f':calendar_spiral: A new event has been scheduled.'
                message = await channel.send(text, embed=msg)
                if DEBUG == False: await message.publish()

                await self.store_message_expire(message, e._get_expire_datetime())

    async def store_message_expire(self, message, expire_datetime):
        mydb = db_connection()
        cursor = mydb.cursor()

        cursor.execute("INSERT event_messages (message_id, expire_datetime) VALUES (%s, %s)", 
            (
                message.id,
                expire_datetime
            )
        )
        mydb.commit()

    async def save_data(self):
        """
        Save all data so far to MySQL
        """

        for event in self.events.values():
            mydb = db_connection()
            cursor = mydb.cursor()

            cursor.execute(
                "INSERT INTO events (id, name, img, url, description, start_time, end_time, published) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE name = VALUES(name), img = VALUES(img), url = VALUES(url), description = VALUES(description), start_time = VALUES(start_time), end_time = VALUES(end_time), published = VALUES(published)",
                (
                    event.id,
                    event.name,
                    event.img,
                    event.url,
                    event.desc,
                    
                    event.start,
                    event.end,

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
        return datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
