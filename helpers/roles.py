import aiohttp
import os
from aiohttp.client import request
import json

import requests

from helpers.config import CC_API_URL, CC_API_TOKEN

class Roles():
    
    def __init__(self):
        """
        Create a Booking object
        """

    async def get_mentors(self):
        """
        Get all bookings from the API
        """
        request = requests.get(CC_API_URL + '/roles', headers={'Authorization': 'Bearer ' + CC_API_TOKEN, 'Accept': 'application/json'})
        if request.status_code == requests.codes.ok:
            feedback = request.json()
            return feedback["data"]["mentors"]
        else:
            return False

    async def get_moderators(self):
        """
        Get all bookings from the API
        """
        request = requests.get(CC_API_URL + '/roles', headers={'Authorization': 'Bearer ' + CC_API_TOKEN, 'Accept': 'application/json'})
        if request.status_code == requests.codes.ok:
            feedback = request.json()
            return feedback["data"]["moderators"]
        else:
            return False