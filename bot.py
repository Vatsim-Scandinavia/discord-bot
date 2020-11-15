from discord.ext import commands, tasks
from helpers import config
import os
from dotenv import load_dotenv
import discord

load_dotenv('.env')

BOT_TOKEN = str(os.getenv('BOT_TOKEN'))

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=config.PREFIXES, description=config.DESCRIPTION, intents=intents)

config.load_cogs(bot)

"""
    Bot event that sets bots rich presence in Discord profile
"""
@bot.event
async def on_ready() -> None:

    print(f'Bot started. \nUsername: {bot.user.name}. \nID: {bot.user.id}')

    await bot.change_presence(activity=config.activity(), status=config.status())

    print('Presence changed.')

if __name__ == "__main__":
    bot.run(BOT_TOKEN)