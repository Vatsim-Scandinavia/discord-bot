import requests
import os

async def get_division_members():
    """
    Get all the division members from the API
    """

    result = []

    # Call the recursive function
    await __fetch_page(result)

    # Return back all collected data
    return result
    

async def __fetch_page(result, url = "https://api.vatsim.net/api/subdivisions/SCA/members/?paginated"):
    """
    Recursive functions to fetch each page's data
    """

    request = requests.get(url, headers={'Authorization': 'Token ' + os.getenv('VATSIM_API_TOKEN')})
    if request.status_code == requests.codes.ok:
        feedback = request.json()
    
        data = feedback["results"]
        result.extend(data)

        next = feedback["next"]
        if next is not None:
            await __fetch_page(result, next)
        else:
            return result
