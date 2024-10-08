import aiohttp
import os
from aiohttp.client import request
import json

import requests

from helpers.config import CC_API_URL, CC_API_TOKEN

class Roles():
    
    def __init__(self):
        """
        Create a Roles object
        """

    async def get_roles(self):
        """
        Get all mentors from the API
        """
        request = requests.get(CC_API_URL + '/users', headers={'Authorization': 'Bearer ' + CC_API_TOKEN, 'Accept': 'application/json'},
        params={
            'include[]': 'roles'
        })
        if request.status_code == requests.codes.ok:
            feedback = request.json()
            return feedback["data"]
        else:
            return False
        
    async def get_training(self):
        """
        Get all traning data from the API
        """
        request = requests.get(CC_API_URL + '/users', headers={'Authorization': 'Bearer ' + CC_API_TOKEN, 'Accept': 'application/json'}, 
        params={
            'include[]': 'training'
        })
        if request.status_code == requests.codes.ok:
            feedback = request.json()
            return feedback["data"]
        else:
            return False