import aiohttp
from typing import List, Dict, Any, Optional

class EventService:
    def __init__(self, *, base_url: str, calendar_type: str, token: str):
        self.base_url = base_url
        self.calendar_type = calendar_type
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

    async def _fetch_data(self, endpoint: str, params: Optional[dict] = None) -> Optional[List[Any]]:
        """
        Generic method to fetch data from the API.

        Args:
            endpoint (str): The API endpoint to query.
            params (dict, optional): Query parameters to include in the request.

        Returns:
            Optional[List[Any]]: The parsed JSON response data or None if the request fails.
        """
        url = f"{self.base_url}/{endpoint}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    response.raise_for_status()
                    resp = await response.json()
                    data = resp.get("data", [])
                    if data:
                        return data
                    
                    return resp
            except aiohttp.ClientError as e:
                print(f"HTTP error occurred while accessing {url}: {e}")
                return None

    async def get_calendar_events(self) -> List[Dict[str, Any]]:
        """Get all events from a specific calendar"""
        return await self._fetch_data(f"calendars/{self.calendar_type}/events")

    async def get_event_titles(self, exclude_titles: List[str] = None) -> List[str]:
        """Get list of unique event titles, optionally excluding specific titles"""
        events = await self.get_calendar_events()
        if not events:
            return ['None is available. Please try again later.']

        titles = []
        exclude_titles = set(exclude_titles or [])
        
        for event in events:
            title = str(event.get('title', ''))
            if title and title not in exclude_titles:
                titles.append(title)

        return list(set(titles))

    async def get_event_details(self, title: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific event by title"""
        events = await self.get_calendar_events()
        if not events:
            return None
        
        return next((event for event in events if event.get("title") == title), None)

