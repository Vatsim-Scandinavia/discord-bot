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
send one request per guild member every run. The HTTP side lives in
``helpers.vatsim_api``.
"""

import asyncio
import json
import time
from collections.abc import Awaitable, Callable, Iterable
from enum import StrEnum
from pathlib import Path
from typing import TypedDict

import aiofiles
import discord
import structlog

from helpers.config import config
from helpers.handler import Handler
from helpers.vatsim_api import (
    NOT_LINKED,
    UNKNOWN,
    Lookup,
    LookupStatus,
    vatsim_api,
)

__all__ = [
    'NOT_LINKED',
    'UNKNOWN',
    'CidLookupUnavailableError',
    'CidResolver',
    'CidSource',
    'Lookup',
    'LookupStatus',
    'cid_resolver',
]

logger = structlog.stdlib.get_logger()

UNAVAILABLE_BACKOFF = 300.0
"""Seconds to wait before asking the API again about a member it failed on."""


class CidSource(StrEnum):
    NICKNAME = 'nickname'
    SHADOW = 'shadow'
    API = 'api'


Fetch = Callable[[int], Awaitable[Lookup]]
"""Look up the CID linked to a Discord user ID. Must not raise."""


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
        unavailable_backoff: float = UNAVAILABLE_BACKOFF,
        concurrency: int | None = None,
        clock: Callable[[], float] = time.time,
        file: str = 'cid_cache.json',
    ) -> None:
        """
        Every argument left as ``None`` is read from ``config``.

        ``fetch`` defaults to the shared ``vatsim_api`` client. It and
        ``clock`` exist so tests can replace the API and time.
        """
        self._cache_file = (cache_dir or config.CACHE_DIR).joinpath(file)
        self.source = CidSource(source or config.CID_SOURCE)
        self._fetch = fetch or vatsim_api.get_discord_link
        self._ttl = config.CID_CACHE_TTL if ttl is None else ttl
        self._negative_ttl = (
            config.CID_NEGATIVE_CACHE_TTL if negative_ttl is None else negative_ttl
        )
        self._unavailable_backoff = unavailable_backoff
        self._semaphore = asyncio.Semaphore(
            concurrency or config.CID_LOOKUP_CONCURRENCY
        )
        self._clock = clock
        self._cache: dict[str, CacheEntry] | None = None
        self._dirty = False
        self._lock = asyncio.Lock()
        self._inflight: dict[int, asyncio.Task[Lookup]] = {}
        self._unavailable: dict[int, float] = {}
        """Discord ID -> when the API last failed on it. In memory only."""
        self._log = logger.bind(cid_source=str(self.source))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def resolve(
        self, member: discord.Member, *, refresh: bool = False
    ) -> int | None:
        """
        Get the member's CID from the configured source.

        Args:
            member: The Discord guild member.
            refresh: Ask the API even if the cached entry is still fresh, for
                example when the member's nickname changed and they may have
                relinked another VATSIM account.

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
            return await self._resolve_shadow(member, refresh=refresh)

        return await self._resolve_api(member, refresh=refresh)

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
            if Handler.has_vatsim_member_role(member)
            and self._fresh(member.id) is None
            and not self._backing_off(member.id)
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

    async def lookup(self, member_id: int, *, refresh: bool = False) -> Lookup:
        """Look up a Discord user ID through the cache and then the API."""
        return await self._lookup(member_id, persist=True, refresh=refresh)

    # ------------------------------------------------------------------
    # Modes
    # ------------------------------------------------------------------

    async def _resolve_shadow(
        self, member: discord.Member, *, refresh: bool
    ) -> int | None:
        nick_cid: int | None = None
        nick_error: ValueError | None = None
        try:
            nick_cid = Handler.get_cid(member)
        except ValueError as e:
            nick_error = e

        result = await self.lookup(member.id, refresh=refresh)
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

    async def _resolve_api(self, member: discord.Member, *, refresh: bool) -> int:
        result = await self.lookup(member.id, refresh=refresh)
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

    async def _lookup(
        self, member_id: int, *, persist: bool, refresh: bool = False
    ) -> Lookup:
        self._load()
        if not refresh:
            cached = self._fresh(member_id)
            if cached is not None:
                return cached

        if self._backing_off(member_id):
            return self._unavailable_answer(member_id)

        # Share one request between concurrent lookups of the same member, so
        # an older response can never overwrite a newer one.
        task = self._inflight.get(member_id)
        if task is None:
            task = asyncio.ensure_future(self._fetch_and_store(member_id, refresh))
            self._inflight[member_id] = task
            task.add_done_callback(
                lambda done: self._inflight.pop(member_id, None)
                if self._inflight.get(member_id) is done
                else None
            )

        result = await asyncio.shield(task)
        if persist:
            await self._save()

        return result

    async def _fetch_and_store(self, member_id: int, refresh: bool) -> Lookup:
        async with self._semaphore:
            # Another lookup may have filled the entry while this one waited.
            cached = None if refresh else self._fresh(member_id)
            if cached is not None:
                return cached

            result = await self._fetch(member_id)

        if result.status is LookupStatus.UNKNOWN:
            # Not written to the cache, so a later run asks again; remembered in
            # memory for a while so this run does not repeat the request.
            self._unavailable[member_id] = self._clock()
            return self._unavailable_answer(member_id)

        self._unavailable.pop(member_id, None)
        self._store(member_id, result.cid)
        return result

    def _backing_off(self, member_id: int) -> bool:
        failed_at = self._unavailable.get(member_id)
        return (
            failed_at is not None
            and self._clock() - failed_at < self._unavailable_backoff
        )

    def _unavailable_answer(self, member_id: int) -> Lookup:
        """An expired linked entry is still a better answer than none."""
        stale = self._entry(member_id)
        if stale is not None and stale['cid'] is not None:
            self._log.debug('Using expired CID cache entry', discord_id=member_id)
            return Lookup(LookupStatus.LINKED, stale['cid'])

        return UNKNOWN

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


cid_resolver = CidResolver()
"""The resolver shared by every cog, so they share one cache."""
