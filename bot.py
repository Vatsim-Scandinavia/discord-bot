import asyncio
import signal

import discord
import sentry_sdk
import structlog
from discord.ext.commands import Bot

from core.logging import configure_logging
from helpers.config import config

# Configure logging before anything is logged so structlog and every stdlib
# logger (discord.py, uvicorn, aiohttp, …) share one consistent output format.
configure_logging(debug=config.DEBUG)

logger = structlog.stdlib.get_logger()

intents = discord.Intents.all()
intents.message_content = True

bot = Bot(
    command_prefix=config.PREFIX,
    description=config.DESCRIPTION,
    intents=intents,
    help_command=None,
    case_sensitive=True,
)


if not config.DEBUG:
    sentry_sdk.init(
        dsn=config.SENTRY_KEY,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
    )


# Event: Set bot presence and sync commands
@bot.event
async def on_ready() -> None:
    global guild
    guild = bot.get_guild(config.GUILD_ID)

    logger.info('Bot started', username=bot.user.name, user_id=bot.user.id)

    try:
        await bot.change_presence(activity=config.activity(), status=config.status())
        await (
            bot.tree.sync()
        )  # Sync global commands (might take up to 1 hour to reflect globally)

    except discord.HTTPException:
        logger.exception('Failed to sync commands due to rate limiting')

    except Exception:
        logger.exception('Unexpected error during on_ready startup')


async def send_dm(user, message):
    """Attempts to send a DM to the user and handles cases where DMs are closed."""
    try:
        await user.send(message)
    except discord.Forbidden:
        logger.warning('Could not send DM; user has DMs disabled', user=user.name)


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: discord.app_commands.AppCommandError
):
    print('thing')
    """Handles errors for application commands."""
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    error_map = {
        discord.app_commands.MissingPermissions: 'You do not have the required permissions to use this command.',
        discord.app_commands.BotMissingPermissions: 'The bot is missing the required permissions to execute this command.',
        discord.Forbidden: 'The bot is missing the required permissions to execute this command.',
        discord.app_commands.CommandNotFound: 'The command you are trying to use does not exist.',
        discord.app_commands.CheckFailure: 'You do not meet the requirements to run this command.',
        discord.app_commands.CommandOnCooldown: lambda e: f'Command is on cooldown. Try again in {e.retry_after:.2f} seconds.',
        discord.app_commands.MissingRole: lambda e: f'You need the `{e.missing_role}` role to use this command.',
        discord.app_commands.MissingAnyRole: lambda e: f'You need one of these roles: `{", ".join(e.missing_roles)}`.',
    }

    error_message = error_map.get(type(error), f'An unexpected error occurred: {error}')

    if callable(error_message):  # Handle dynamic error messages
        error_message = error_message(error)

    try:
        await interaction.followup.send(error_message, ephemeral=True)

    except discord.HTTPException:
        logger.exception('Error sending error message')

    logger.error('Command error', error=str(error))


@bot.event
async def on_error(event, *args, **kwargs):
    logger.exception(
        'Unhandled error in event', event_name=event, args=args, kwargs=kwargs
    )


@bot.event
async def on_message(message: discord.Message):
    if message.type == discord.MessageType.pins_add and message.author == bot.user:
        await message.delete()


# Load all cogs at startup
@bot.event
async def on_connect():
    await config.load_cogs(bot)


# Signal handling for graceful shutdown
def handle_exit_signal(signal_number, _):
    logger.info('Received shutdown signal; closing bot', signal=signal_number)
    asyncio.create_task(bot.close())


# Register signals
signal.signal(signal.SIGINT, handle_exit_signal)  # For CTRL + C
signal.signal(signal.SIGTERM, handle_exit_signal)  # For termination signal

# Start the bot
if __name__ == '__main__':
    try:
        bot.run(config.BOT_TOKEN, log_handler=None)
    except Exception:
        logger.exception('Error starting the bot')
