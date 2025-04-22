from discord.ext.commands import Cog
from discord.types.gateway import MessageReactionAddEvent


class CoreRoles(Cog):
    """Handles core roles such as VATSIM affiliation and division membership"""

    def __init__(self):
        pass

    @Cog.listener('on_raw_reaction_add')
    async def on_raw_reaction_add(self, payload: MessageReactionAddEvent):
        if payload.guild_id is None or payload.user_id == bot.user.id:
            return

        guild = bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)

        if not user:  # User not found
            return

        emoji_name = emoji.demojize(
            payload.emoji.name
        )  # Convert emoji to :emoji_name: format
        message_id = str(payload.message_id)  # Ensure consistency with config

        if (
            message_id in config.REACTION_MESSAGE_IDS
            and emoji_name in config.REACTION_ROLES
        ):
            role_id = int(config.REACTION_ROLES[emoji_name])
            role = discord.utils.get(guild.roles, id=role_id)

            if role and role not in user.roles:
                await user.add_roles(role, reason=config.ROLE_REASONS['reaction_add'])
                await send_dm(
                    user,
                    f'You have been given the `{role.name}` role because you reacted with {payload.emoji}',
                )
