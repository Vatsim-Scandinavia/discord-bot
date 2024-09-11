import aiohttp
import asyncio

from datetime import datetime, timedelta
from helpers.message import event_description, get_image
from helpers.config import EVENT_API_TOKEN, EVENT_CALENDAR_URL

class Event():
    #
    # ----------------------------------
    #   INITIAL
    # ----------------------------------
    #

    def __init__(self, id, name, img, url, desc, start_time: datetime, end_time: datetime, published):
        """
        Create an Event object
        """
        self.id = id
        self.name = name
        self.img = img
        self.url = url
        self.desc = desc
        
        self.start = start_time
        self.end = end_time

        self.published = published

    #
    # ----------------------------------
    #   BOOLEAN FUNCTIONS
    # ----------------------------------
    #
    def is_expired(self) -> bool:
        """
        Check if event is expired and no longer valid
        """
        return datetime.utcnow() > self.start
    
    def should_be_notified(self) -> bool:
        """
        Check if this event triggers a notification
        """

        start = self.start
        now = datetime.utcnow()

        if self.published is not None:
            return False
        
        # Define the when it's 2 hours prior, and the threshold of notifying to avoid notifications way too late
        notificationTime = start - timedelta(hours=2)
        notificationThreshold = start - timedelta(hours=1.75)

        return (now >= notificationTime and now <= notificationThreshold)
    
    #
    # ----------------------------------
    #   DATA PARSING FUNCTIONS
    # ----------------------------------
    #
    async def fetch_api_updates(self):
        """
        Fetch API updates for this object
        """
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {EVENT_API_TOKEN}'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{EVENT_CALENDAR_URL}/events/{str(self.id)}', headers=headers) as resp:
                if resp.status == 404:
                    return False
                
                if resp.status != 200:
                    print(f"Response from API was not OK. Status: {resp.status}", flush=True)
                    return False
                
                updated_event = await resp.json()
                updated_event = updated_event.get('event')

                self.name = updated_event.get('title')
                self.img = updated_event.get('image')
                self.url = updated_event.get('link')
                self.desc = event_description(updated_event.get('long_description'))
                
                self.start = datetime.strptime(updated_event.get('start_date'), "%Y-%m-%d %H:%M:%S")
                self.end = datetime.strptime(updated_event.get('end_date'), "%Y-%m-%d %H:%M:%S")

            return True
    
    def mark_as_published(self):
        """
        Mark event as published
        """

        self.published = datetime.utcnow()

    def _get_expire_datetime(self):
        """
        Return the expire datetime for message deletion for selected event
        """

        return self.start + timedelta(hours=24)