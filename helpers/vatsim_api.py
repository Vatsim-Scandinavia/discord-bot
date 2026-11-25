"""
Client for the VATSIM APIs the bot talks to.

One ``VatsimApi`` owns one ``aiohttp`` session, shared by every call. The
APIs authenticate differently (the v2 Core API takes ``X-API-Key``, the v1
member list takes ``Authorization: Token``), so headers are sent per request
rather than set on the session.
"""

import asyncio
import json
import math
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from enum import Enum
from http import HTTPStatus
from typing import Any, TypedDict

import aiohttp
import structlog

from helpers.config import config

logger = structlog.stdlib.get_logger()

MIN_VATSIM_CID = 800000
"""Lowest number accepted as a VATSIM CID."""

MAX_RETRY_AFTER = 60.0
"""Longest wait, in seconds, honoured from a 429 Retry-After header."""

DEFAULT_RETRY_AFTER = 5.0
"""Wait, in seconds, after a 429 without a usable Retry-After header."""


class DivisionMember(TypedDict):
    """Division member data."""

    id: int
    subdivision: str


class VATSIMDivisionMemberFetchException(Exception):
    def __init__(self) -> None:
        super().__init__('An error occurred while fetching VATSIM division members.')


class LookupStatus(Enum):
    LINKED = 'linked'
    """The member linked Discord on the VATSIM community portal."""

    NOT_LINKED = 'not_linked'
    """The API answered 404: no VATSIM account is linked to this Discord user."""

    UNKNOWN = 'unknown'
    """The API could not be asked (network error, 5xx, rate limited, bad body)."""


@dataclass(frozen=True)
class Lookup:
    status: LookupStatus
    cid: int | None = None


UNKNOWN = Lookup(LookupStatus.UNKNOWN)
NOT_LINKED = Lookup(LookupStatus.NOT_LINKED)


@dataclass(frozen=True)
class RawResponse:
    """The parts of an HTTP response the client looks at."""

    status: int
    data: Any = None
    retry_after: str | None = None


Send = Callable[[str, Mapping[str, str]], Awaitable[RawResponse]]
"""GET a URL with the given headers. May raise on network or JSON errors."""


class VatsimApi:
    def __init__(
        self,
        *,
        core_url: str | None = None,
        token: str | None = None,
        send: Send | None = None,
        sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
        clock: Callable[[], float] = time.time,
        timeout: float = 10,
    ) -> None:
        """
        ``core_url`` and ``token`` left as ``None`` are read from ``config``.

        ``send``, ``sleep`` and ``clock`` exist so tests can replace the HTTP
        layer and time.
        """
        self._core_url = core_url
        self._token = token
        self._send = send or self._http_send
        self._sleep = sleep
        self._clock = clock
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    @property
    def core_url(self) -> str:
        return (self._core_url or config.VATSIM_CORE_API_URL).rstrip('/')

    @property
    def token(self) -> str:
        return config.VATSIM_API_TOKEN if self._token is None else self._token

    async def get_discord_link(self, discord_id: int) -> Lookup:
        """
        Look up which VATSIM CID a Discord user linked, retrying once after a 429.

        Never raises: anything that stops the API from giving an answer
        returns ``UNKNOWN``, so callers can fall back instead of acting on it.
        """
        log = logger.bind(discord_id=discord_id)
        url = f'{self.core_url}/members/discord/{discord_id}'
        headers = {'X-API-Key': self.token}

        for attempt in range(2):
            try:
                response = await self._send(url, headers)
            except (aiohttp.ClientError, TimeoutError, json.JSONDecodeError) as e:
                log.warning('Core API request failed', error=str(e))
                return UNKNOWN

            if response.status != HTTPStatus.TOO_MANY_REQUESTS:
                return _interpret(response, discord_id, log)

            delay = _retry_after_seconds(response.retry_after, self._clock())
            log.warning('Core API rate limited', retry_after=delay, attempt=attempt)
            if attempt == 0:
                await self._sleep(delay)

        return UNKNOWN

    async def get_division_members(self) -> list[DivisionMember]:
        """
        Fetch every member of the subdivision, following pagination.

        Raises:
            ValueError: ``VATSIM_CHECK_MEMBER_URL`` is not configured.
            VATSIMDivisionMemberFetchException: Any page failed. Fails hard and
                early, so callers never act on a partial member list.

        """
        url: str | None = config.VATSIM_CHECK_MEMBER_URL
        if not url:
            raise ValueError('VATSIM_CHECK_MEMBER_URL is not configured or is None')

        headers = {'Authorization': f'Token {self.token}'}
        result: list[DivisionMember] = []
        while url:
            try:
                response = await self._send(url, headers)
                if response.status != HTTPStatus.OK:
                    msg = f'HTTP {response.status} from {url}'
                    raise RuntimeError(msg)
                data = response.data.get('results', [])
                url = response.data.get('next')
            except Exception as e:
                raise VATSIMDivisionMemberFetchException from e

            if not data:
                break

            result.extend(data)

            if url and url.startswith('http://'):
                url = url.replace('http://', 'https://', 1)

        return result

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

        self._session = None

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout)
            )

        return self._session

    async def _http_send(self, url: str, headers: Mapping[str, str]) -> RawResponse:
        async with self._get_session().get(url, headers=headers) as response:
            data = (
                await response.json(content_type=None)
                if response.status == HTTPStatus.OK
                else None
            )
            return RawResponse(
                status=response.status,
                data=data,
                retry_after=response.headers.get('Retry-After'),
            )


def _interpret(response: RawResponse, discord_id: int, log: Any) -> Lookup:
    if response.status == HTTPStatus.NOT_FOUND:
        return NOT_LINKED

    if response.status != HTTPStatus.OK:
        log.warning('Core API returned an error', status=response.status)
        return UNKNOWN

    try:
        return Lookup(LookupStatus.LINKED, _cid_from_body(response.data, discord_id))
    except (KeyError, TypeError, ValueError):
        log.warning('Core API returned an unexpected body', body=response.data)
        return UNKNOWN


def _cid_from_body(data: Any, discord_id: int) -> int:
    """
    Pick the CID out of a ``{"id": str, "user_id": str}`` response.

    The docs do not say which field holds the CID. ``user_id`` is the likely
    one (a foreign key to the VATSIM user, with ``id`` the Discord ID), so it
    is tried first. A field only counts if it is a plausible CID: at least
    ``MIN_VATSIM_CID`` and not the Discord ID we asked about.

    Raises:
        KeyError, TypeError, ValueError: The body holds no plausible CID.

    """
    for field in ('user_id', 'id'):
        candidate = int(data[field])
        if candidate >= MIN_VATSIM_CID and candidate != discord_id:
            return candidate

    raise ValueError('No field holds a valid CID')


def _retry_after_seconds(value: str | None, now: float) -> float:
    """
    Turn a Retry-After header into a delay in seconds.

    The header is either a number of seconds or an HTTP date. Anything else,
    including ``nan`` and ``inf``, gives ``DEFAULT_RETRY_AFTER``.
    """
    delay = DEFAULT_RETRY_AFTER
    if value is not None:
        try:
            delay = float(value)
        except ValueError:
            try:
                delay = parsedate_to_datetime(value).timestamp() - now
            except (TypeError, ValueError):
                delay = DEFAULT_RETRY_AFTER

    if not math.isfinite(delay):
        delay = DEFAULT_RETRY_AFTER

    return min(max(delay, 0.0), MAX_RETRY_AFTER)


vatsim_api = VatsimApi()
"""The client shared by the whole bot, so every VATSIM call reuses one session."""
