import asyncio
import json
from pathlib import Path
from typing import TypedDict

import aiofiles
import structlog

logger = structlog.stdlib.get_logger()


class MemberNick(TypedDict):
    """Cached member information"""

    name: str | None
    nick: str
    cid: int


class MemberCache:
    """
    Possibly unsafe member cache for storing original nicknames of members.

    Should be sort of thread-safe with asyncio.Lock.
    """

    def __init__(self, folder: Path, file: str = 'member_cache.json'):
        self._cache_file = folder.joinpath(file)
        self._nicknames: dict[str, MemberNick] = {}
        self._lock = asyncio.Lock()
        self._log = logger.bind(path=self._cache_file)
        self._load_cache()

    def _load_cache(self) -> None:
        """Load nickname cache from file"""
        try:
            if self._cache_file.exists():
                with open(self._cache_file) as f:
                    self._nicknames = json.load(f)
        except Exception:
            self._log.exception('Failed to load nickname cache')
            self._nicknames = {}

    async def _save_cache(self) -> None:
        """Save nickname cache to file"""
        try:
            async with aiofiles.open(self._cache_file, 'w') as f:
                await f.write(json.dumps(self._nicknames))
        except Exception:
            self._log.exception('Failed to save nickname cache')

    async def store(
        self, member_id: int, nick: str, name: str | None, cid: int
    ) -> None:
        """Store original nickname for a member"""
        async with self._lock:
            self._nicknames[str(member_id)] = MemberNick(name=name, nick=nick, cid=cid)
            await self._save_cache()

    def get(self, member_id: int) -> MemberNick | None:
        """Retrieve original nickname for a member"""
        return self._nicknames.get(str(member_id))

    def get_member_ids(self) -> list[int]:
        """Get all member IDs in the cache"""
        return [int(member_id) for member_id in self._nicknames]

    async def remove_nickname(self, member_id: int) -> None:
        """Remove nickname from cache"""
        async with self._lock:
            if str(member_id) in self._nicknames:
                del self._nicknames[str(member_id)]
                await self._save_cache()
