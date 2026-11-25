import asyncio
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from email.utils import format_datetime

import aiohttp
import pytest

from helpers.config import config
from helpers.vatsim_api import (
    DEFAULT_RETRY_AFTER,
    MAX_RETRY_AFTER,
    LookupStatus,
    RawResponse,
    VatsimApi,
    VATSIMDivisionMemberFetchException,
    _retry_after_seconds,
)

API_CID = 1111111
DISCORD_ID = 123456789012345678
NOW = 1_000_000.0
TOKEN = 'test-token'  # noqa: S105 - fake value for tests


def linked(cid: int = API_CID, discord_id: int = DISCORD_ID) -> RawResponse:
    return RawResponse(200, {'id': str(discord_id), 'user_id': str(cid)})


class FakeSend:
    """Stands in for the HTTP layer, replaying queued responses."""

    def __init__(self, *responses: RawResponse | Exception) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def __call__(self, url: str, headers: Mapping[str, str]) -> RawResponse:
        self.calls.append((url, dict(headers)))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def make_api(send: FakeSend, slept: list[float] | None = None) -> VatsimApi:
    async def sleep(seconds: float) -> None:
        if slept is not None:
            slept.append(seconds)

    return VatsimApi(
        core_url='https://core.test/v2/',
        token=TOKEN,
        send=send,
        sleep=sleep,
        clock=lambda: NOW,
    )


def lookup(api: VatsimApi):
    return asyncio.run(api.get_discord_link(DISCORD_ID))


# --- Discord link lookup ---------------------------------------------------


def test_linked_member_returns_cid_and_sends_api_key() -> None:
    send = FakeSend(linked())

    result = lookup(make_api(send))

    assert result.status is LookupStatus.LINKED
    assert result.cid == API_CID
    assert send.calls == [
        (
            f'https://core.test/v2/members/discord/{DISCORD_ID}',
            {'X-API-Key': TOKEN},
        )
    ]


def test_404_means_not_linked() -> None:
    assert lookup(make_api(FakeSend(RawResponse(404)))).status is (
        LookupStatus.NOT_LINKED
    )


@pytest.mark.parametrize(
    'failure',
    [
        RawResponse(500),
        RawResponse(502),
        aiohttp.ClientConnectionError('connection refused'),
        TimeoutError(),
        json.JSONDecodeError('Expecting value', '{', 1),
        RawResponse(200, {'unexpected': 'shape'}),
        RawResponse(200, None),
    ],
)
def test_failures_are_unknown(failure: RawResponse | Exception) -> None:
    assert lookup(make_api(FakeSend(failure))).status is LookupStatus.UNKNOWN


def test_cid_is_read_from_id_when_user_id_echoes_discord_id() -> None:
    send = FakeSend(RawResponse(200, {'id': str(API_CID), 'user_id': str(DISCORD_ID)}))

    assert lookup(make_api(send)).cid == API_CID


@pytest.mark.parametrize('bad_cid', [0, 1, 799999])
def test_cid_below_minimum_is_unknown(bad_cid: int) -> None:
    send = FakeSend(RawResponse(200, {'id': str(DISCORD_ID), 'user_id': str(bad_cid)}))

    assert lookup(make_api(send)).status is LookupStatus.UNKNOWN


def test_rate_limit_waits_for_retry_after_and_retries_once() -> None:
    slept: list[float] = []
    send = FakeSend(RawResponse(429, retry_after='3'), linked())

    assert lookup(make_api(send, slept)).cid == API_CID
    assert slept == [3.0]
    assert len(send.calls) == 2


def test_rate_limit_twice_gives_up() -> None:
    send = FakeSend(RawResponse(429, retry_after='999'), RawResponse(429))

    assert lookup(make_api(send)).status is LookupStatus.UNKNOWN
    assert len(send.calls) == 2


# --- Retry-After parsing ---------------------------------------------------


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (None, DEFAULT_RETRY_AFTER),
        ('3', 3.0),
        ('-5', 0.0),
        ('999', MAX_RETRY_AFTER),
        ('nan', DEFAULT_RETRY_AFTER),
        ('inf', DEFAULT_RETRY_AFTER),
        ('soon', DEFAULT_RETRY_AFTER),
    ],
)
def test_retry_after_seconds(value: str | None, expected: float) -> None:
    assert _retry_after_seconds(value, NOW) == expected


def test_retry_after_http_date() -> None:
    date = format_datetime(datetime.fromtimestamp(NOW + 12, tz=UTC), usegmt=True)

    assert _retry_after_seconds(date, NOW) == 12.0
    assert _retry_after_seconds(date, NOW + 20) == 0.0


# --- Division members ------------------------------------------------------


def test_division_members_follow_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        config, 'VATSIM_CHECK_MEMBER_URL', 'https://api.test/members/?paginated'
    )
    first = {'id': 1000001, 'subdivision': 'SCA'}
    second = {'id': 1000002, 'subdivision': 'SCA'}
    send = FakeSend(
        RawResponse(
            200, {'results': [first], 'next': 'http://api.test/members/?page=2'}
        ),
        RawResponse(200, {'results': [second], 'next': None}),
    )

    members = asyncio.run(make_api(send).get_division_members())

    assert members == [first, second]
    assert [url for url, _ in send.calls] == [
        'https://api.test/members/?paginated',
        'https://api.test/members/?page=2',
    ]
    assert send.calls[0][1] == {'Authorization': f'Token {TOKEN}'}


@pytest.mark.parametrize(
    'failure',
    [RawResponse(500), aiohttp.ClientConnectionError(), RawResponse(200, None)],
)
def test_division_member_failure_raises(
    monkeypatch: pytest.MonkeyPatch, failure: RawResponse | Exception
) -> None:
    monkeypatch.setattr(config, 'VATSIM_CHECK_MEMBER_URL', 'https://api.test/members/')

    with pytest.raises(VATSIMDivisionMemberFetchException):
        asyncio.run(make_api(FakeSend(failure)).get_division_members())


def test_division_members_need_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, 'VATSIM_CHECK_MEMBER_URL', '')

    with pytest.raises(ValueError, match='VATSIM_CHECK_MEMBER_URL'):
        asyncio.run(make_api(FakeSend()).get_division_members())
