"""
Resolve a Discord member's VATSIM CID (issue #223).

The CID used to come only from the member's nickname (``Handler.get_cid``).
The VATSIM Core API can also map a Discord user ID to a CID, for members who
linked Discord on the community portal. ``config.CID_SOURCE`` picks the source:

- ``nickname``: parse the nickname only, the old behaviour.
- ``shadow``: return the nickname CID, but also ask the API and log whenever
  the two disagree. This is for measuring coverage before switching over.
- ``api``: ask the API first and fall back to the nickname.

Lookups are cached on disk, keyed by Discord ID, so the daily loops do not
send one request per guild member every run.
"""

import asyncio
import json
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from enum import Enum, StrEnum
from http import HTTPStatus
from pathlib import Path
from typing import Any, TypedDict

import aiofiles
import aiohttp
import discord
import structlog

from helpers.config import config
from helpers.handler import Handler

logger = structlog.stdlib.get_logger()

MAX_RETRY_AFTER = 60.0
"""Longest wait, in seconds, honoured from a 429 Retry-After header."""

DEFAULT_RETRY_AFTER = 5.0
"""Wait, in seconds, after a 429 without a usable Retry-After header."""


class CidSource(StrEnum):
    NICKNAME = 'nickname'
    SHADOW = 'shadow'
    API = 'api'


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
    """The parts of an HTTP response the resolver looks at."""

    status: int
    data: Any = None
    retry_after: str | None = None


Fetch = Callable[[int], Awaitable[RawResponse]]
"""Fetch the Core API response for a Discord user ID. May raise on network errors."""


class CacheEntry(TypedDict):
    cid: int | None
    fetched_at: float


class CidLookupUnavailableError(Exception):
    """
    Neither the API nor the nickname gave a CID, and the API could not be asked.

    Deliberately not a ``ValueError``: callers treat ``ValueError`` as "this
    member has no CID" and strip their roles. An API outage must not do that,
    so callers should skip the member and leave their roles alone.
    """

    def __init__(self, member_id: int) -> None:
        super().__init__(f'Could not look up the CID of Discord user {member_id}')
        self.member_id = member_id


class CidResolver:
    def __init__(
        self,
        cache_dir: Path | None = None,
        *,
        source: CidSource | str | None = None,
        fetch: Fetch | None = None,
        ttl: float | None = None,
        negative_ttl: float | None = None,
        concurrency: int | None = None,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
        file: str = 'cid_cache.json',
    ) -> None:
        """
        Every argument left as ``None`` is read from ``config``.

        ``fetch``, ``clock`` and ``sleep`` exist so tests can replace the HTTP
        layer and time.
        """
        self._cache_file = (cache_dir or config.CACHE_DIR).joinpath(file)
        self.source = CidSource(source or config.CID_SOURCE)
        self._fetch = fetch or self._http_fetch
        self._ttl = config.CID_CACHE_TTL if ttl is None else ttl
        self._negative_ttl = (
            config.CID_NEGATIVE_CACHE_TTL if negative_ttl is None else negative_ttl
        )
        self._semaphore = asyncio.Semaphore(
            concurrency or config.CID_LOOKUP_CONCURRENCY
        )
        self._clock = clock
        self._sleep = sleep
        self._session: aiohttp.ClientSession | None = None
        self._cache: dict[str, CacheEntry] | None = None
        self._dirty = False
        self._lock = asyncio.Lock()
        self._log = logger.bind(cid_source=str(self.source))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def resolve(self, member: discord.Member) -> int | None:
        """
        Get the member's CID from the configured source.

        Returns:
            None if the member lacks the VATSIM member role, otherwise the CID.

        Raises:
            ValueError: The member has the role but no CID could be found, the
                same contract as ``Handler.get_cid``.
            CidLookupUnavailableError: In ``api`` mode, the API could not be
                asked and the nickname holds no CID either.

        """
        if not Handler.has_vatsim_member_role(member):
            return None

        if self.source is CidSource.NICKNAME:
            return Handler.get_cid(member)

        if self.source is CidSource.SHADOW:
            return await self._resolve_shadow(member)

        return await self._resolve_api(member)

    async def warm(self, members: Iterable[discord.Member]) -> None:
        """
        Look up every member whose cache entry is missing or expired.

        Bulk loops call this before their per-member loop, so a cold cache is
        filled with at most ``concurrency`` requests in flight instead of one
        request after another. The cache file is written once at the end.
        """
        if self.source is CidSource.NICKNAME:
            return

        self._load()
        pending = [
            member.id
            for member in members
            if Handler.has_vatsim_member_role(member) and self._fresh(member.id) is None
        ]
        if not pending:
            return

        started = self._clock()
        results = await asyncio.gather(
            *(self._lookup(member_id, persist=False) for member_id in pending)
        )
        await self._save()

        self._log.info(
            'Warmed CID cache',
            requested=len(pending),
            linked=sum(r.status is LookupStatus.LINKED for r in results),
            not_linked=sum(r.status is LookupStatus.NOT_LINKED for r in results),
            unknown=sum(r.status is LookupStatus.UNKNOWN for r in results),
            seconds=round(self._clock() - started, 1),
        )

    async def lookup(self, member_id: int) -> Lookup:
        """Look up a Discord user ID through the cache and then the API."""
        return await self._lookup(member_id, persist=True)

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

        self._session = None

    # ------------------------------------------------------------------
    # Modes
    # ------------------------------------------------------------------

    async def _resolve_shadow(self, member: discord.Member) -> int | None:
        nick_cid: int | None = None
        nick_error: ValueError | None = None
        try:
            nick_cid = Handler.get_cid(member)
        except ValueError as e:
            nick_error = e

        result = await self.lookup(member.id)
        log = self._log.bind(
            discord_id=member.id,
            nick=member.nick,
            nick_cid=nick_cid,
            api_cid=result.cid,
        )

        if result.status is LookupStatus.UNKNOWN:
            log.warning('Core API unavailable for CID check', cid_check='cid_api_error')
        elif result.status is LookupStatus.NOT_LINKED:
            log.info('Member has not linked Discord', cid_check='cid_api_missing')
        elif nick_cid is None:
            log.info('Nickname has no CID, API does', cid_check='cid_nick_missing')
        elif nick_cid != result.cid:
            log.warning('Nickname and API CID differ', cid_check='cid_mismatch')
        else:
            log.debug('Nickname and API CID match', cid_check='cid_match')

        if nick_error is not None:
            raise nick_error

        return nick_cid

    async def _resolve_api(self, member: discord.Member) -> int:
        result = await self.lookup(member.id)
        if result.status is LookupStatus.LINKED and result.cid is not None:
            return result.cid

        log = self._log.bind(
            discord_id=member.id, nick=member.nick, api_status=result.status.value
        )
        try:
            cid = Handler.get_cid(member)
        except ValueError:
            if result.status is LookupStatus.UNKNOWN:
                raise CidLookupUnavailableError(member.id) from None

            log.info('No CID from the API or the nickname')
            raise

        log.info('CID taken from nickname, not the API', nick_cid=cid)

        # Handler.get_cid only returns None for members without the role, and
        # resolve() has already filtered those out.
        if cid is None:
            raise ValueError

        return cid

    # ------------------------------------------------------------------
    # Lookup and cache
    # ------------------------------------------------------------------

    async def _lookup(self, member_id: int, *, persist: bool) -> Lookup:
        self._load()
        cached = self._fresh(member_id)
        if cached is not None:
            return cached

        async with self._semaphore:
            # Another task may have filled the entry while this one waited.
            cached = self._fresh(member_id)
            if cached is not None:
                return cached

            result = await self._request(member_id)

        if result.status is LookupStatus.UNKNOWN:
            # Not cached, so the next run asks again. An expired linked entry is
            # still a better answer than none while the API is down.
            stale = self._entry(member_id)
            if stale is not None and stale['cid'] is not None:
                self._log.debug('Using expired CID cache entry', discord_id=member_id)
                return Lookup(LookupStatus.LINKED, stale['cid'])

            return result

        self._store(member_id, result.cid)
        if persist:
            await self._save()

        return result

    async def _request(self, member_id: int) -> Lookup:
        """Ask the API, retrying once after a 429."""
        log = self._log.bind(discord_id=member_id)

        for attempt in range(2):
            try:
                response = await self._fetch(member_id)
            except (aiohttp.ClientError, TimeoutError) as e:
                log.warning('Core API request failed', error=str(e))
                return UNKNOWN

            if response.status != HTTPStatus.TOO_MANY_REQUESTS:
                return self._interpret(response, member_id, log)

            delay = _retry_after_seconds(response.retry_after)
            log.warning('Core API rate limited', retry_after=delay, attempt=attempt)
            if attempt == 0:
                await self._sleep(delay)

        return UNKNOWN

    @staticmethod
    def _interpret(response: RawResponse, member_id: int, log: Any) -> Lookup:
        if response.status == HTTPStatus.NOT_FOUND:
            return NOT_LINKED

        if response.status != HTTPStatus.OK:
            log.warning('Core API returned an error', status=response.status)
            return UNKNOWN

        try:
            return Lookup(LookupStatus.LINKED, _cid_from_body(response.data, member_id))
        except (KeyError, TypeError, ValueError):
            log.warning('Core API returned an unexpected body', body=response.data)
            return UNKNOWN

    async def _http_fetch(self, member_id: int) -> RawResponse:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={'X-API-Key': config.VATSIM_API_TOKEN},
                timeout=aiohttp.ClientTimeout(total=10),
            )

        url = f'{config.VATSIM_CORE_API_URL.rstrip("/")}/members/discord/{member_id}'
        async with self._session.get(url) as response:
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

    def _entry(self, member_id: int) -> CacheEntry | None:
        self._load()
        assert self._cache is not None  # noqa: S101 - set by _load
        return self._cache.get(str(member_id))

    def _fresh(self, member_id: int) -> Lookup | None:
        """Return the cached lookup if it has not expired."""
        entry = self._entry(member_id)
        if entry is None:
            return None

        ttl = self._ttl if entry['cid'] is not None else self._negative_ttl
        if self._clock() - entry['fetched_at'] >= ttl:
            return None

        if entry['cid'] is None:
            return NOT_LINKED

        return Lookup(LookupStatus.LINKED, entry['cid'])

    def _store(self, member_id: int, cid: int | None) -> None:
        self._load()
        assert self._cache is not None  # noqa: S101 - set by _load
        self._cache[str(member_id)] = CacheEntry(cid=cid, fetched_at=self._clock())
        self._dirty = True

    def _load(self) -> None:
        """Read the cache file the first time it is needed."""
        if self._cache is not None:
            return

        self._cache = {}
        try:
            if self._cache_file.exists():
                with open(self._cache_file) as f:
                    self._cache = json.load(f)
        except Exception:
            self._log.exception('Failed to load CID cache', path=self._cache_file)
            self._cache = {}

    async def _save(self) -> None:
        async with self._lock:
            if not self._dirty:
                return

            self._dirty = False
            try:
                async with aiofiles.open(self._cache_file, 'w') as f:
                    await f.write(json.dumps(self._cache))
            except Exception:
                self._log.exception('Failed to save CID cache', path=self._cache_file)


def _cid_from_body(data: Any, member_id: int) -> int:
    """
    Pick the CID out of a ``{"id": str, "user_id": str}`` response.

    The docs do not say which field holds the CID. ``user_id`` is the likely
    one (a foreign key to the VATSIM user, with ``id`` the Discord ID), but if
    ``user_id`` turns out to echo the Discord ID we asked about, ``id`` must be
    the CID instead.

    Raises:
        KeyError, TypeError, ValueError: The body is not in the expected shape.

    """
    user_id = int(data['user_id'])
    if user_id != member_id:
        return user_id

    other = int(data['id'])
    if other == member_id:
        raise ValueError('Neither field holds a CID')

    return other


def _retry_after_seconds(value: str | None) -> float:
    try:
        delay = float(value) if value is not None else DEFAULT_RETRY_AFTER
    except ValueError:
        delay = DEFAULT_RETRY_AFTER

    return min(max(delay, 0.0), MAX_RETRY_AFTER)


cid_resolver = CidResolver()
"""The resolver shared by every cog, so they share one cache and one session."""
