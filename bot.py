import discord
import sentry_sdk
import signal
import asyncio
import emoji

from discord.ext import commands
from discord.ext.commands import BadArgument, CommandInvokeError
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

    # Create an instance of Handler
    handler = Handler()

    # Extract cid from nickname, exit early if not found
    cid = await handler.get_cid(user)

    try:
        api_data = await handler.get_division_members()

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

async def send_dm(user, message):
    """Attempts to send a DM to the user and handles cases where DMs are closed."""
    try:
        await user.send(message)
    except discord.Forbidden:
        print(f"Could not send DM to {user.name}. They have DMs disabled.")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id is None or payload.user_id == bot.user.id:
        return
    
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if not user: # User not found
        return
    
    emoji_name = emoji.demojize(payload.emoji.name) # Convert emoji to :emoji_name: format
    message_id = str(payload.message_id) # Ensure consistency with config

    if message_id in config.REACTION_MESSAGE_IDS and emoji_name in config.REACTION_ROLES:
        role_id = int(config.REACTION_ROLES[emoji_name])
        role = discord.utils.get(guild.roles, id=role_id)

        if role and role not in user.roles:
            await user.add_roles(role, reason=config.ROLE_REASONS['reaction_add'])
            await send_dm(user, f'You have been given the `{role.name}` role because you reacted with {payload.emoji}')

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.guild_id is None or payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)

    if not user:  # User not found
        return
    
    emoji_name = emoji.demojize(payload.emoji.name)  # Convert emoji to :emoji_name: format
    message_id = str(payload.message_id)  # Ensure consistency with config

    if message_id in config.REACTION_MESSAGE_IDS and emoji_name in config.REACTION_ROLES:
        role_id = int(config.REACTION_ROLES[emoji_name])
        role = discord.utils.get(guild.roles, id=role_id)

        if role and role in user.roles:
            await user.remove_roles(role, reason=config.ROLE_REASONS['reaction_remove'])
            await send_dm(user, f'You no longer have the `{role.name}` role because you removed your reaction.')

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    """
    Handles errors for application commands.
    """
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    error_map = {
        discord.app_commands.MissingPermissions: "You do not have the required permissions to use this command.",
        discord.app_commands.BotMissingPermissions: "The bot is missing the required permissions to execute this command.",
        discord.app_commands.CommandNotFound: "The command you are trying to use does not exist.",
        discord.app_commands.CheckFailure: "You do not meet the requirements to run this command.",
        discord.app_commands.CommandOnCooldown: lambda e: f"Command is on cooldown. Try again in {e.retry_after:.2f} seconds.",
        discord.app_commands.MissingRole: lambda e: f"You need the `{e.missing_role}` role to use this command.",
        discord.app_commands.MissingAnyRole: lambda e: f"You need one of these roles: `{', '.join(e.missing_roles)}`.",
    }

    error_message = error_map.get(type(error), f"An unexpected error occurred: {error}")

    if callable(error_message): # Handle dynamic error messages
        error_message = error_message(error)

    try:
        await interaction.followup.send(error_message, ephemeral=True)

    except discord.HTTPException as e:
        print(f"Error sending error message: {e}")

    print(f"Command Error: {error}")

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Error in {event}: {args} {kwargs}", flush=True)

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

    
