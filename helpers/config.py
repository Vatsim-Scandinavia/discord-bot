import discord

PREFIXES = [
    '!', '.', '?',
]

DESCRIPTION = 'This is a new VATSCA Discord Bot'

PRESENCE_TEXT = 'VATSCA Airspace'

def prefix() -> list:
    return PREFIXES

def activity() -> discord.Activity:
    return discord.Activity(type=discord.ActivityType.watching, name=PRESENCE_TEXT)

def status() -> discord.Status:
    return discord.Status.online