import asyncio
import signal

import discord
import sentry_sdk
from discord.ext.commands import BadArgument, Bot, CommandInvokeError

from helpers.config import config

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

    print(f'Bot started. \nUsername: {bot.user.name}. \nID: {bot.user.id}', flush=True)

    try:
        await bot.change_presence(activity=config.activity(), status=config.status())
        await (
            bot.tree.sync()
        )  # Sync global commands (might take up to 1 hour to reflect globally)

    except CommandInvokeError as e:
        print(f'Error in command invocation: {e}', flush=True)

    except BadArgument as e:
        print(f'Error changing presence. Exception - {e}', flush=True)

    except discord.HTTPException as e:
        print(f'Failed to sync commands due to rate limiting: {e}', flush=True)


async def send_dm(user, message):
    """Attempts to send a DM to the user and handles cases where DMs are closed."""
    try:
        await user.send(message)
    except discord.Forbidden:
        print(f'Could not send DM to {user.name}. They have DMs disabled.')


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

    except discord.HTTPException as e:
        print(f'Error sending error message: {e}')

    print(f'Command Error: {error}')


@bot.event
async def on_error(event, *args, **kwargs):
    print(f'Error in {event}: {args} {kwargs}', flush=True)


@bot.event
async def on_message(message: discord.Message):
    if message.type == discord.MessageType.pins_add and message.author == bot.user:
        await message.delete()


# Load all cogs at startup
@bot.event
async def on_connect():
    await config.load_cogs(bot)


# Signal handling for graceful shutdown
def handle_exit_signal(signal_number, frame):
    print('Received shutdown signal. Closing bot...', flush=True)
    asyncio.create_task(bot.close())


# Register signals
signal.signal(signal.SIGINT, handle_exit_signal)  # For CTRL + C
signal.signal(signal.SIGTERM, handle_exit_signal)  # For termination signal

# Start the bot
if __name__ == '__main__':
    try:
        discord.utils.setup_logging()
        bot.run(config.BOT_TOKEN)
    except Exception as e:
        print(f'Error starting the bot. Exception - {e}', flush=True)
