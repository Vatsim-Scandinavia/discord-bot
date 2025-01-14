
class BotException(Exception):
    """
    Base exception class for all bot exceptions to provide a common error handling pattern.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

class GuildNotFoundException(BotException):
    """
    Exception raised when a guild is not found.
    """
    def __init__(self, guild_id: int):
        self.message = f"Guild with ID {guild_id} not found."
        super().__init__(self.message)

class CIDNotFoundException(BotException):
    """
    Exception raised when a CID is not found in the user's nickname.
    """
    def __init__(self, user_id: int):
        self.message = f"CID not found for user with ID {user_id}."
        super().__init__(self.message)