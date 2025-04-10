import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

import aiofiles

logger = logging.getLogger(__name__)

class MemberCache:
    """
    Possibly unsafe member cache for storing original nicknames of members.

    Should be sort of thread-safe with asyncio.Lock.
    """

    def __init__(self, folder: Path, file: str = "member_cache.json"):
        self._cache_file = folder.joinpath(file)
        self._nicknames: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._load_cache()

    def _load_cache(self) -> None:
        """Load nickname cache from file"""
        try:
            if self._cache_file.exists():
                with open(self._cache_file) as f:
                    self._nicknames = json.load(f)
        except Exception as e:
            logger.exception(f"Failed to load nickname cache: {e}")
            self._nicknames = {}

    async def _save_cache(self) -> None:
        """Save nickname cache to file"""
        try:
            async with aiofiles.open(self._cache_file, 'w') as f:
                await f.write(json.dumps(self._nicknames))
        except Exception as e:
            logger.exception(f"Failed to save nickname cache: {e}")

    async def store_nickname(self, member_id: int, nickname: str) -> None:
        """Store original nickname for a member"""
        async with self._lock:
            self._nicknames[str(member_id)] = nickname
            await self._save_cache()

    def get_nickname(self, member_id: int) -> Optional[str]:
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
