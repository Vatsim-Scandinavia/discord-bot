import aiohttp
import os
from aiohttp.client import request
import json

import requests

from helpers.config import CC_API_URL, CC_API_TOKEN

class Booking():
    
    def __init__(self):
        """
        Create a Booking object
        """
    
    async def get_bookings(self):
        """
        Get all bookings from the API
        """
        request = requests.get(CC_API_URL + '/bookings', headers={'Authorization': 'Bearer ' + CC_API_TOKEN, 'Accept': 'application/json'})
        if request.status_code == requests.codes.ok:
            feedback = request.json()
            return feedback["data"]

    async def post_booking(self, cid: int, date: str, start_at: str, end_at: str, position: str, tag: int):
        """
        Post a new booking to the API
        """

        data = {
            'cid': cid,
            'date': date,
            'start_at': start_at,
            'end_at': end_at,
            'position': position,
            'tag': tag,
            'source': 'DISCORD'
        }

        request = requests.post(url=CC_API_URL + "/bookings/create", headers={'Authorization': 'Bearer ' + CC_API_TOKEN, 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}, data=data)
        
        return request

    async def delete_booking(self, cid: int, booking_id: int):
        """
        Delete a booking from the API
        """
        request = requests.delete(url=CC_API_URL + "/bookings/" + str(booking_id), headers={'Authorization': 'Bearer ' + CC_API_TOKEN, 'Accept': 'application/json'})
        if request.status_code == requests.codes.ok:
            return 200
        else:
            return request.status_code