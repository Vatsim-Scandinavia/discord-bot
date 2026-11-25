import asyncio
import json
from pathlib import Path

import pytest
from structlog.testing import capture_logs

from helpers.config import config
from helpers.vatsim_ids import (
    NOT_LINKED,
    UNKNOWN,
    CidLookupUnavailableError,
    CidResolver,
    Lookup,
    LookupStatus,
)
from tests.conftest import FakeMember, FakeRole

VATSIM_ROLE = FakeRole(100, 'VATSIM Member')
NICK_CID = 1234567
API_CID = 1111111
DISCORD_ID = 123456789012345678


@pytest.fixture(autouse=True)
def vatsim_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, 'VATSIM_MEMBER_ROLE', VATSIM_ROLE.id)


def make_member(
    nick: str | None = f'John Doe - {NICK_CID}',
    member_id: int = DISCORD_ID,
    roles: list[FakeRole] | None = None,
) -> FakeMember:
    member = FakeMember([VATSIM_ROLE], [VATSIM_ROLE] if roles is None else roles)
    member.id = member_id
    member.nick = nick
    return member


def linked(cid: int = API_CID) -> Lookup:
    return Lookup(LookupStatus.LINKED, cid)


class FakeApi:
    """Stands in for ``VatsimApi.get_discord_link``, replaying queued results."""

    def __init__(self, *responses: Lookup) -> None:
        self.responses = list(responses)
        self.default: Lookup = linked()
        self.calls: list[int] = []
        self.in_flight = 0
        self.max_in_flight = 0

    async def __call__(self, member_id: int) -> Lookup:
        self.calls.append(member_id)
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(0)
            return self.responses.pop(0) if self.responses else self.default
        finally:
            self.in_flight -= 1


class Clock:
    def __init__(self) -> None:
        self.now = 1_000_000.0

    def __call__(self) -> float:
        return self.now


def make_resolver(
    tmp_path: Path, source: str, api: FakeApi, clock: Clock | None = None, **kwargs
) -> CidResolver:
    kwargs.setdefault('unavailable_backoff', 0)
    return CidResolver(
        tmp_path,
        source=source,
        fetch=api,
        ttl=100,
        negative_ttl=10,
        concurrency=kwargs.pop('concurrency', 5),
        clock=clock or Clock(),
        **kwargs,
    )


def checks(logs: list[dict]) -> list[str]:
    return [entry['cid_check'] for entry in logs if 'cid_check' in entry]


# --- Role gate and nickname mode -------------------------------------------


@pytest.mark.parametrize('source', ['nickname', 'shadow', 'api'])
def test_member_without_vatsim_role_returns_none(tmp_path: Path, source: str) -> None:
    api = FakeApi()
    resolver = make_resolver(tmp_path, source, api)

    assert asyncio.run(resolver.resolve(make_member(roles=[]))) is None
    assert api.calls == []


def test_nickname_mode_never_calls_api(tmp_path: Path) -> None:
    api = FakeApi()
    resolver = make_resolver(tmp_path, 'nickname', api)

    assert asyncio.run(resolver.resolve(make_member())) == NICK_CID

    with pytest.raises(ValueError, match=r'^$'):
        asyncio.run(resolver.resolve(make_member(nick='John Doe')))

    asyncio.run(resolver.warm([make_member()]))
    assert api.calls == []


# --- Shadow mode -----------------------------------------------------------


def test_shadow_mode_returns_nickname_cid_and_logs_mismatch(tmp_path: Path) -> None:
    api = FakeApi(linked(API_CID))
    with capture_logs() as logs:
        resolver = make_resolver(tmp_path, 'shadow', api)
        cid = asyncio.run(resolver.resolve(make_member()))

    assert cid == NICK_CID
    assert checks(logs) == ['cid_mismatch']
    mismatch = next(e for e in logs if e.get('cid_check') == 'cid_mismatch')
    assert mismatch['discord_id'] == DISCORD_ID
    assert mismatch['nick_cid'] == NICK_CID
    assert mismatch['api_cid'] == API_CID


@pytest.mark.parametrize(
    ('response', 'expected'),
    [
        (linked(NICK_CID), 'cid_match'),
        (NOT_LINKED, 'cid_api_missing'),
        (UNKNOWN, 'cid_api_error'),
    ],
)
def test_shadow_mode_logs_api_result(
    tmp_path: Path, response: Lookup, expected: str
) -> None:
    api = FakeApi(response)
    with capture_logs() as logs:
        resolver = make_resolver(tmp_path, 'shadow', api)
        cid = asyncio.run(resolver.resolve(make_member()))

    assert cid == NICK_CID
    assert checks(logs) == [expected]


def test_shadow_mode_keeps_nickname_error_when_api_knows_cid(tmp_path: Path) -> None:
    api = FakeApi(linked(API_CID))
    with capture_logs() as logs:
        resolver = make_resolver(tmp_path, 'shadow', api)
        with pytest.raises(ValueError, match=r'^$'):
            asyncio.run(resolver.resolve(make_member(nick='John Doe')))

    assert checks(logs) == ['cid_nick_missing']


# --- API mode --------------------------------------------------------------


def test_api_mode_prefers_api_cid(tmp_path: Path) -> None:
    api = FakeApi(linked(API_CID))
    resolver = make_resolver(tmp_path, 'api', api)

    assert asyncio.run(resolver.resolve(make_member())) == API_CID


def test_api_mode_works_without_cid_in_nickname(tmp_path: Path) -> None:
    api = FakeApi(linked(API_CID))
    resolver = make_resolver(tmp_path, 'api', api)

    assert asyncio.run(resolver.resolve(make_member(nick=None))) == API_CID


def test_api_mode_falls_back_to_nickname_on_404_and_caches_it(tmp_path: Path) -> None:
    api = FakeApi(NOT_LINKED)
    resolver = make_resolver(tmp_path, 'api', api)

    assert asyncio.run(resolver.resolve(make_member())) == NICK_CID
    assert asyncio.run(resolver.resolve(make_member())) == NICK_CID
    assert api.calls == [DISCORD_ID]


def test_api_mode_raises_value_error_when_unlinked_and_no_nick_cid(
    tmp_path: Path,
) -> None:
    api = FakeApi(NOT_LINKED)
    resolver = make_resolver(tmp_path, 'api', api)

    with pytest.raises(ValueError, match=r'^$'):
        asyncio.run(resolver.resolve(make_member(nick='John Doe')))


def test_api_failure_falls_back_to_nickname_without_caching(tmp_path: Path) -> None:
    api = FakeApi(UNKNOWN, UNKNOWN)
    resolver = make_resolver(tmp_path, 'api', api)

    assert asyncio.run(resolver.resolve(make_member())) == NICK_CID
    assert asyncio.run(resolver.resolve(make_member())) == NICK_CID
    assert api.calls == [DISCORD_ID, DISCORD_ID]
    assert not (tmp_path / 'cid_cache.json').exists()


def test_api_failure_without_nick_cid_is_not_a_value_error(tmp_path: Path) -> None:
    # A ValueError makes callers strip the member's roles; an outage must not.
    api = FakeApi(UNKNOWN)
    resolver = make_resolver(tmp_path, 'api', api)

    with pytest.raises(CidLookupUnavailableError):
        asyncio.run(resolver.resolve(make_member(nick='John Doe')))

    assert not issubclass(CidLookupUnavailableError, ValueError)


def test_api_failure_uses_expired_linked_entry(tmp_path: Path) -> None:
    clock = Clock()
    api = FakeApi(linked(API_CID), UNKNOWN)
    resolver = make_resolver(tmp_path, 'api', api, clock)

    assert asyncio.run(resolver.resolve(make_member(nick=None))) == API_CID
    clock.now += 1000
    assert asyncio.run(resolver.resolve(make_member(nick=None))) == API_CID
    assert len(api.calls) == 2


# --- Cache -----------------------------------------------------------------


def test_linked_entry_expires_after_ttl(tmp_path: Path) -> None:
    clock = Clock()
    api = FakeApi(linked(API_CID), linked(2222222))
    resolver = make_resolver(tmp_path, 'api', api, clock)

    assert asyncio.run(resolver.resolve(make_member())) == API_CID
    clock.now += 99
    assert asyncio.run(resolver.resolve(make_member())) == API_CID
    assert len(api.calls) == 1

    clock.now += 1
    assert asyncio.run(resolver.resolve(make_member())) == 2222222
    assert len(api.calls) == 2


def test_negative_entry_uses_shorter_ttl(tmp_path: Path) -> None:
    clock = Clock()
    api = FakeApi(NOT_LINKED, linked(API_CID))
    resolver = make_resolver(tmp_path, 'api', api, clock)

    assert asyncio.run(resolver.lookup(DISCORD_ID)).status is LookupStatus.NOT_LINKED
    clock.now += 9
    assert asyncio.run(resolver.lookup(DISCORD_ID)).status is LookupStatus.NOT_LINKED
    clock.now += 1
    assert asyncio.run(resolver.lookup(DISCORD_ID)).cid == API_CID
    assert len(api.calls) == 2


def test_cache_survives_restart(tmp_path: Path) -> None:
    clock = Clock()
    first = make_resolver(tmp_path, 'api', FakeApi(linked(API_CID)), clock)
    asyncio.run(first.resolve(make_member()))

    stored = json.loads((tmp_path / 'cid_cache.json').read_text())
    assert stored == {str(DISCORD_ID): {'cid': API_CID, 'fetched_at': clock.now}}

    api = FakeApi()
    second = make_resolver(tmp_path, 'api', api, clock)
    assert asyncio.run(second.resolve(make_member())) == API_CID
    assert api.calls == []


def test_corrupt_cache_file_is_ignored(tmp_path: Path) -> None:
    (tmp_path / 'cid_cache.json').write_text('{not json')
    api = FakeApi(linked(API_CID))
    resolver = make_resolver(tmp_path, 'api', api)

    assert asyncio.run(resolver.resolve(make_member())) == API_CID


# --- Concurrency and backoff ---------------------------------------------


def test_concurrent_lookups_of_one_member_share_a_request(tmp_path: Path) -> None:
    api = FakeApi(linked(API_CID), linked(2222222))
    resolver = make_resolver(tmp_path, 'api', api)

    async def both() -> list[Lookup]:
        return await asyncio.gather(
            resolver.lookup(DISCORD_ID), resolver.lookup(DISCORD_ID)
        )

    results = asyncio.run(both())

    assert [r.cid for r in results] == [API_CID, API_CID]
    assert api.calls == [DISCORD_ID]


def test_unavailable_member_is_not_asked_again_within_backoff(tmp_path: Path) -> None:
    clock = Clock()
    api = FakeApi(UNKNOWN, linked(API_CID))
    resolver = make_resolver(tmp_path, 'api', api, clock, unavailable_backoff=60)
    member = make_member()

    asyncio.run(resolver.warm([member]))
    assert asyncio.run(resolver.resolve(member)) == NICK_CID
    asyncio.run(resolver.warm([member]))
    assert api.calls == [DISCORD_ID]

    clock.now += 60
    assert asyncio.run(resolver.resolve(member)) == API_CID
    assert api.calls == [DISCORD_ID, DISCORD_ID]


def test_refresh_skips_fresh_cache_entry(tmp_path: Path) -> None:
    api = FakeApi(linked(API_CID), linked(2222222))
    resolver = make_resolver(tmp_path, 'api', api)

    assert asyncio.run(resolver.resolve(make_member())) == API_CID
    assert asyncio.run(resolver.resolve(make_member())) == API_CID
    assert asyncio.run(resolver.resolve(make_member(), refresh=True)) == 2222222
    assert asyncio.run(resolver.resolve(make_member())) == 2222222
    assert len(api.calls) == 2


def test_refresh_during_outage_keeps_cached_cid(tmp_path: Path) -> None:
    api = FakeApi(linked(API_CID), UNKNOWN)
    resolver = make_resolver(tmp_path, 'api', api)

    assert asyncio.run(resolver.resolve(make_member(nick=None))) == API_CID
    assert asyncio.run(resolver.resolve(make_member(nick=None), refresh=True)) == (
        API_CID
    )


# --- Warm ------------------------------------------------------------------


def test_warm_limits_concurrency_and_fills_cache(tmp_path: Path) -> None:
    api = FakeApi()
    resolver = make_resolver(tmp_path, 'shadow', api, concurrency=3)
    members = [make_member(member_id=i) for i in range(1, 21)]
    outsider = make_member(member_id=99, roles=[])

    asyncio.run(resolver.warm([*members, outsider]))

    assert sorted(api.calls) == list(range(1, 21))
    assert api.max_in_flight <= 3

    for member in members:
        asyncio.run(resolver.resolve(member))
    assert len(api.calls) == 20

    stored = json.loads((tmp_path / 'cid_cache.json').read_text())
    assert len(stored) == 20


def test_warm_skips_fresh_entries(tmp_path: Path) -> None:
    api = FakeApi()
    resolver = make_resolver(tmp_path, 'api', api)
    member = make_member()

    asyncio.run(resolver.resolve(member))
    asyncio.run(resolver.warm([member]))

    assert api.calls == [DISCORD_ID]
