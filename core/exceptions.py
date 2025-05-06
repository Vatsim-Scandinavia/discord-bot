from typing import Any


class ExpectedMixin:
    """Base mixin for all expected exceptions."""


class UnexpectedMixin:
    """Base mixin for all unexpected exceptions."""


class GuildNotFound(Exception, UnexpectedMixin):
    """Exception raised when a guild is not found."""

    def __init__(self, guild_id: int, payload: Any):
        super().__init__()
        self.guild_id = guild_id
        self.payload = payload

    def __str__(self):
        """Return a string representation of the exception."""
        return f'Guild with ID {self.guild_id} not found.'
