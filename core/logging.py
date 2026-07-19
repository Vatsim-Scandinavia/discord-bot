"""
Centralised logging configuration.

structlog is the single source of truth for log output. Standard-library
logging — everything discord.py, uvicorn, aiohttp and fastapi emit — is routed
*through* the same structlog processor chain via ``ProcessorFormatter`` so every
line, ours or a dependency's, is rendered identically.

Call :func:`configure_logging` exactly once, as early as possible, before any
logger is used.
"""

import logging
import sys

import structlog

# Processors applied to BOTH structlog-native events and foreign stdlib records,
# so the two produce identical output. Rendering happens later, in the
# ProcessorFormatter, not here.
_SHARED_PROCESSORS: list = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,  # e.g. "cogs.roles" — the module location
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt='iso', utc=True),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]


def configure_logging(*, debug: bool = False) -> None:
    """
    Configure structlog and stdlib logging to share one output format.

    Args:
        debug: When true, log at DEBUG level with a colourised, human-friendly
            console renderer. Otherwise log at INFO level as logfmt
            (`key=value` pairs), which our aggregation and Sentry parse in
            production while staying readable in a raw log tail.

    """
    level = logging.DEBUG if debug else logging.INFO

    renderer = (
        structlog.dev.ConsoleRenderer()
        if debug
        else structlog.processors.LogfmtRenderer()
    )

    # structlog-native loggers: run the shared chain, then hand the event dict
    # off to the stdlib ProcessorFormatter instead of rendering here.
    structlog.configure(
        processors=[
            *_SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # One formatter renders every record — foreign stdlib records get the shared
    # chain applied via ``foreign_pre_chain`` first.
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_SHARED_PROCESSORS,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()  # drop anything discord.utils.setup_logging() installed
    root.addHandler(handler)
    root.setLevel(level)
