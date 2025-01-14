import requests
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    """
    Foundational data for a user in Control Center.
    """
    id: int
    email: str
    first_name: str
    last_name: str
    rating: str
    region: str
    division: str
    subdivision: str
    atc_active: bool
    atc_active_areas: dict[str, bool]


class Roles(BaseModel):
    __root__: List[str]


class UserWithRoles(UserBase):
    roles: dict[str, Optional[Roles]]


class UserRoles(BaseModel):
    __root__: list[UserWithRoles]


class Endorsement(BaseModel):
    valid_from: datetime
    valid_to: Optional[datetime]
    rating: str
    areas: List[str]


class UserWithEndorsement(UserBase):
    endorsements: dict[str, list[Endorsement]]


class UserEndorsements(BaseModel):
    __root__: list[UserWithEndorsement]


class Training(BaseModel):
    area: str
    type: str
    status: int
    status_description: str
    created_at: datetime
    started_at: Optional[datetime]
    ratings: list[str]


class UserWithTrainings(UserBase):
    training: List[Training]


class UserTrainings(UserBase):
    __root__: list[UserWithTrainings]


class ControlCenterClient:
    """
    A client for the VATSCA Control Center API.

    See https://docs.vatsca.org/controlcenter/latest/api/
    """

    def __init__(self, *, api_url: str, api_token: str):
        """
        Initialize the ControlCenterClient with a shared requests session.
        """
        self._session = requests.Session()
        self._base_url = api_url
        self._session.headers.update(
            {"Authorization": f"Bearer {api_token}", "Accept": "application/json"}
        )

    def _get_data(self, endpoint, params=None):
        """
        Helper method to perform a GET request.

        :todo: Consider removing this as it is unused at the moment.
        """
        response = self._get_raw(endpoint, params)
        return response.json()

    def _get_raw(self, endpoint, params=None):
        """
        Helper method to perform a GET request.
        """
        url = f"{self._base_url}{endpoint}"
        response = self._session.get(url, params=params)
        response.raise_for_status()
        return response

    def get_roles(self) -> UserRoles:
        """
        Get all mentors from the API.
        """
        data = self._get_raw("/users", params={"include[]": "roles"})
        return UserRoles.model_validate(data.content)

    def get_endorsements(self) -> UserEndorsements:
        """
        Get all endorsements from the API.
        """
        data = self._get_raw("/endorsements/examiners")
        return UserEndorsements.model_validate(data.content)

    def get_training(self) -> UserTrainings:
        """
        Get all training data from the API.
        """
        data = self._get_raw("/users", params={"include[]": "training"})
        return UserTrainings.model_validate_json(data.content)
