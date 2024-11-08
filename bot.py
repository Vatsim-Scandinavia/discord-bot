import discord
import os
import sentry_sdk
import signal
import re
import asyncio

from discord.ext import commands
from discord.ext.commands import BadArgument, CommandInvokeError
from discord import app_commands
from helpers.config import config
from helpers.handler import Handler

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix=config.PREFIX, description=config.DESCRIPTION, intents=intents, help_command=None, case_sensitive=True)


if not config.DEBUG:
    sentry_sdk.init(
        dsn=config.SENTRY_KEY,

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0
    )

# Event: Set bot presence and sync commands
@bot.event
async def on_ready() -> None:
    global guild
    guild = bot.get_guild(config.GUILD_ID)

    print(f'Bot started. \nUsername: {bot.user.name}. \nID: {bot.user.id}', flush=True)

    try:
        await bot.change_presence(activity=config.activity(), status=config.status())
        await bot.tree.sync() # Sync global commands (might take up to 1 hour to reflect globally)

    except CommandInvokeError as e:
        print(f"Error in command invocation: {e}", flush=True)

    except BadArgument as e:
        print(f'Error changing presence. Exception - {e}', flush=True)
    
    except discord.HTTPException as e:
        print(f"Failed to sync commands due to rate limiting: {e}", flush=True)

@bot.event
async def on_member_update(before_update, user: discord.Member):
    """
    Function checks member and assigns role according to the username.
    :param before_update:
    :param user:
    :return:
    """

    # Return if the nickname hasn't changed
    if before_update.nick == user.nick:
        return
    
    # Define role objects
    vatsca_member = discord.utils.get(user.guild.roles, id=config.VATSCA_MEMBER_ROLE)
    vatsim_member = discord.utils.get(user.guild.roles, id=config.VATSIM_MEMBER_ROLE)

    # Extract cid from nickname, exit early if not found
    cid_match = re.search(r'\d+', str(user.nick))

    if not cid_match:
        return
    
    cid = int(cid_match.group())

    try:
        api_data = await Handler.get_division_members()

        should_have_vatsca = any(
            int(entry['id']) == cid and str(entry["subdivision"]) == str(config.VATSIM_SUBDIVISION)
            for entry in api_data
        )

        # Manage role assignments
        tasks = []

        if vatsim_member in user.roles:
            # add VATSCA if required otherwise remove it
            if should_have_vatsca and vatsca_member not in user.roles:
                tasks.append(user.add_roles(vatsca_member))
            elif not should_have_vatsca and vatsca_member in user.roles:
                tasks.append(user.remove_roles(vatsca_member))
        
        elif vatsca_member in user.roles:
            tasks.append(user.remove_roles(vatsca_member)) # Remove VATSCA if the user doesnt have VATSIM role

        if tasks:
            await asyncio.gather(*tasks)
    except discord.Forbidden as e:
        print(f"Bot lacks permission for this action: {e}", flush=True)

    except discord.HTTPException as e:
        print(f"HTTP error: {e}", flush=True)

    except Exception as e:
        print(f"Unexpected error: {e}", flush=True)


# Load all cogs at startup
@bot.event
async def on_connect():
    await config.load_cogs(bot)

# Signal handling for graceful shutdown
def handle_exit_signal(signal_number, frame):
    print("Received shutdown signal. Closing bot...", flush=True)
    asyncio.create_task(bot.close())

# Register signals
signal.signal(signal.SIGINT, handle_exit_signal) # For CTRL + C
signal.signal(signal.SIGTERM, handle_exit_signal) # For termination signal

# Start the bot
if __name__ == '__main__':
    try:
        bot.run(config.BOT_TOKEN)
    except Exception as e:
        print(f'Error starting the bot. Exception - {e}', flush=True)

    
