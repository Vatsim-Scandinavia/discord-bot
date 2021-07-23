import aiohttp
import os

from datetime import datetime, timedelta
from helpers.message import embed, event_description, get_image

class Event():

    #
    # ----------------------------------
    #   INITIAL
    # ----------------------------------
    #

    API_URL = 'https://vatsim-scandinavia.org/api/calendar/events'

    def __init__(self, id, name, img, url, desc, start: datetime, recurring, recurring_interval, recurring_end, published):
        """
        Create an Event object
        """
        self.id = id
        self.name = name
        self.img = img
        self.url = url
        self.desc = desc
        
        self.start = start
        self.recurring = recurring
        self.recurring_interval = recurring_interval
        self.recurring_end = recurring_end

        self.published = published







    #
    # ----------------------------------
    #   BOOLEAN FUNCTIONS
    # ----------------------------------
    #

    def is_recurring_event(self) -> bool:
        """
        Check if event is recurring
        """

        return self.recurring is not None

    def is_expired(self) -> bool:
        """
        Check if event is expired and no longer valid
        """
        if self.is_recurring_event():
            return datetime.utcnow() > self.recurring_end
        else:
            return datetime.utcnow() > self.start

    def should_be_notified(self) -> bool:
        """
        Check if this event triggers a notification
        """
        
        start = self.start
        now = datetime.utcnow()

        is_recurring = self.is_recurring_event()

        # Change the start date if recurrence is the thing
        if is_recurring:
            recurred_date = self._get_recurred_date(start, self.recurring, self.recurring_interval, self.recurring_end)

            # If today is notification day and we've not already notified
            if recurred_date is not False:
                # Go on if it's never been published
                if self.published is None:
                    start = recurred_date
                # Go on if it's not passed two hours since last publish
                elif now > self.published + timedelta(hours = 2):
                    start = recurred_date
                else:
                    return False
            else:
                return False
        else:
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

        auth = aiohttp.BasicAuth(os.getenv('FORUM_API_TOKEN'), '')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.API_URL + "/" + str(self.id), auth=auth) as resp:
                
                if resp.status == 404:
                    return False
                
                updated_event = await resp.json()

                if updated_event.get('hidden'):
                    return False

                self.name = updated_event.get('title')
                self.img = get_image(updated_event.get('description'))
                self.url = updated_event.get('url')
                self.desc = event_description(updated_event.get('description'))
                
                self.start = datetime.strptime(updated_event.get('start'), "%Y-%m-%dT%H:%M:%SZ")

                self.hidden = updated_event.get('hidden')

                # If reccurence data is available, parse it
                if updated_event.get('recurrence') is not None:
                    self.parse_recurrence(updated_event.get('recurrence'))
                else:
                    self.recurring = None
                    self.recurring_interval = None
                    self.recurring_end = None

            return True


    def parse_recurrence(self, ics):
        """
        Parse recurrence ICS string
        """

        params = self.__split_ics_params(ics)

        self.recurring = params["freq"]
        self.recurring_interval = params["interval"]
        self.recurring_end = self.__parse_ics_recurrence_end(params, self.start)


    def mark_as_published(self):
        """
        Mark event as published
        """

        self.published = datetime.utcnow()









    #
    # ----------------------------------
    #   PRIVATE FUNCTIONS
    # ----------------------------------
    #

    def __split_ics_params(self, ics: str):
        """
        Split ICS parameters
        """

        params = {}
        for param in ics.split(';'):
            split = param.split('=')
            params[split[0].lower()] = split[1]

        return params


    def __parse_ics_recurrence_end(self, params: list, start_time: datetime):
        """
        Parse and calculate when the last day of recurrence is
        """

        # If until timestamp has been provided, let's use that
        if "until" in params:
            return datetime.strptime(params["until"], "%Y%m%dT%H%M%S")

        # If no timestamp has been given, calculate based on the interval
        if "count" in params:
            if params["freq"] == "DAILY":
                return start_time + timedelta(days = (int(params["count"]) * int(params["interval"])) )
            elif params["freq"] == "WEEKLY":
                return start_time + timedelta(weeks = (int(params["count"]) * int(params["interval"])) )
            elif params["freq"] == "MONTHLY":
                return start_time + timedelta(months = (int(params["count"]) * int(params["interval"])) )

        # If no timestamp selected, none can be calculated, then this is probably an event without end date
        return start_time + timedelta(days=(365*10))


    def _get_recurred_date(self, proposed_date, recurring, interval, recurring_end):
        """
        Function to return back the date of next reccurence or False
        """

        interval = int(interval) or 1

        while(proposed_date <= recurring_end):

                # Is the proposed datetime happening between 2h and 1.75h? It's today then
                if proposed_date <= datetime.utcnow() + timedelta(hours=2) and proposed_date >= datetime.utcnow() + timedelta(hours=1.75) :
                    return proposed_date

                # Break if we're past today
                if proposed_date.date() > datetime.utcnow().date():
                    break

                if recurring == "DAILY":
                    proposed_date = proposed_date + timedelta(days=interval)
                elif recurring == "WEEKLY":
                    proposed_date = proposed_date + timedelta(weeks=interval)
                elif recurring == "MONTHLY":
                    proposed_date = proposed_date + timedelta(months=interval)
                else:
                    return False
        
        return False