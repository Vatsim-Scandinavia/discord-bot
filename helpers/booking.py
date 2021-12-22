import aiohttp
import os
from aiohttp.client import request
import json

import requests

from helpers.config import BOOKING_API_URL, BOOKING_API_TOKEN

class Booking():
    
    def __init__(self):
        """
        Create a Booking object
        """
        """self.cid = cid
        self.date = date
        self.start_at = start_at
        self.end_at = end_at
        self.position = position
        self.tag = tag"""
    
    async def get_bookings(self):
        """
        Get all bookings from the API
        """
        request = requests.get(BOOKING_API_URL, headers={'Authorization': 'Bearer ' + BOOKING_API_TOKEN, 'Accept': 'application/json'})
        if request.status_code == requests.codes.ok:
            feedback = request.json()
            return feedback["bookings"]

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
            'tag': tag
        }

        request = requests.post(url=BOOKING_API_URL + "/create", headers={'Authorization': 'Bearer ' + BOOKING_API_TOKEN, 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}, data=data)
        if request.status_code == requests.codes.ok:
            return 200
        else:
            return request.status_code

        return False

    async def delete_booking(self, cid: int, position: str):
        """
        Delete a booking from the API
        """
        booking = requests.get(BOOKING_API_URL, headers={'Authorization': 'Bearer ' + BOOKING_API_TOKEN, 'Accept': 'application/json'})

        if booking.status_code == requests.codes.ok:
            feedback = booking.json()
            for booking in feedback["bookings"]:
                if booking["cid"] == cid and booking["callsign"] + ":" == position:
                    request = requests.delete(url=BOOKING_API_URL + "/" + str(booking["id"]), headers={'Authorization': 'Bearer ' + BOOKING_API_TOKEN, 'Accept': 'application/json'})
                    if request.status_code == requests.codes.ok:
                        return 200
                    else:
                        return request.status_code
            return 404
        else:
            return booking.status_code

        return False