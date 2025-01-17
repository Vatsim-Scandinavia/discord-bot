import requests


class VATSIMClient:
    def __init__(self, api_url: str, api_key: str):
        self._base_url = api_url
        self._session = requests.Session(
            headers={"Content-Type": "application/json", "X-API-Key": self.api_key}
        )

    def _get(self, endpoint: str):
        response = self._session.get(f"{self._base_url}{endpoint}")
        response.raise_for_status()
        data = response.json()
        return data

    def get_vatsim_cid(self, discord_id: str):
        response = self._session.get(f"/members/discord/{discord_id}")
        return response.json()["data"]["cid"]
