import logging
import shlex

import structlog

from core.logging import configure_logging


def _parse_logfmt(line: str) -> dict[str, str]:
    """Parse a logfmt line into a dict. shlex handles the quoted values."""
    return dict(token.split('=', 1) for token in shlex.split(line))


def test_structlog_and_stdlib_share_one_logfmt_format(capsys) -> None:
    """
    A structlog event and a foreign stdlib record must render identically.

    This is the whole point of the config: discord.py/uvicorn logs (stdlib) and
    our structlog logs come out through the same renderer, so downstream tooling
    sees one consistent format.
    """
    configure_logging(debug=False)

    structlog.stdlib.get_logger('cogs.roles').info('native event', member=42)
    logging.getLogger('discord.gateway').warning('foreign event')

    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(lines) == 2

    native, foreign = (_parse_logfmt(line) for line in lines)

    # Both carry the same structured keys, proving one shared chain.
    for record in (native, foreign):
        assert 'timestamp' in record
        assert 'level' in record
        assert 'logger' in record
        assert 'event' in record

    assert native['event'] == 'native event'
    assert native['level'] == 'info'
    assert native['logger'] == 'cogs.roles'
    assert native['member'] == '42'  # logfmt is untyped text

    assert foreign['event'] == 'foreign event'
    assert foreign['level'] == 'warning'
    assert foreign['logger'] == 'discord.gateway'


def test_debug_flag_controls_level(capsys) -> None:
    """Level filtering replaces scattered ``if config.DEBUG`` guards."""
    configure_logging(debug=False)
    structlog.stdlib.get_logger('cogs.roles').debug('suppressed')
    assert capsys.readouterr().out.strip() == ''

    configure_logging(debug=True)
    structlog.stdlib.get_logger('cogs.roles').debug('emitted')
    assert 'emitted' in capsys.readouterr().out
