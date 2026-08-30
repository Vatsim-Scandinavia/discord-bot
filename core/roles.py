"""
Shared role mechanics.

The cogs decide *which* roles a member should hold; this module carries out the
change against Discord. Keeping it here lets the Control Center sync, the
membership listener and the reaction opt-in share one implementation without
importing each other.

Not to be confused with ``helpers.roles``, which is the Control Center API
client.
"""

import discord
import structlog

from helpers.config import config

logger = structlog.stdlib.get_logger()


async def update_role(
    user: discord.Member,
    role: discord.Role | None,
    condition: bool,
    add_reason: str,
    remove_reason: str,
) -> None:
    """Add or remove a role based on a condition."""
    # discord.utils.get yields None for an unconfigured (id 0) or deleted role and
    # callers pass its result straight in. Adding None raises for every member.
    if role is None:
        logger.warning('Skipping role update, role not found in guild', name=user.name)
        return

    if condition and role not in user.roles:
        await user.add_roles(role, reason=add_reason)
    elif not condition and role in user.roles:
        await user.remove_roles(role, reason=remove_reason)


def membership_role_ids(include_vatsca: bool = False) -> set[int]:
    """Collect every role id the bot manages on behalf of Control Center."""
    role_ids = {
        config.MENTOR_ROLE,
        config.BUDDY_ROLE,
        config.TRAINING_STAFF_ROLE,
        config.VISITOR_ROLE,
    }

    if include_vatsca:
        role_ids.add(config.VATSCA_MEMBER_ROLE)

    role_ids.update(int(role_id) for role_id in config.FIR_MENTORS.values())
    role_ids.update(int(role_id) for role_id in config.FIR_BUDDIES.values())
    role_ids.update(int(role_id) for role_id in config.FIR_EXAMINERS.values())
    role_ids.update(
        int(role_id)
        for ratings in config.TRAINING_ROLES.values()
        for role_id in ratings.values()
    )
    role_ids.update(int(role_id) for role_id in config.CONTROLLER_FIR_ROLES.values())
    role_ids.update(
        int(role_id)
        for ratings in config.RATING_FIR_DATA.values()
        for role_id in ratings.values()
    )

    return {role_id for role_id in role_ids if role_id}


async def cleanup_membership_roles(
    user: discord.Member, reason: str, include_vatsca: bool = False
) -> None:
    """Strip every managed role from a member who is no longer eligible."""
    role_ids = membership_role_ids(include_vatsca=include_vatsca)
    roles_to_remove = [role for role in user.roles if role.id in role_ids]

    if roles_to_remove:
        await user.remove_roles(*roles_to_remove, reason=reason)


async def send_dm(member: discord.Member, message: str) -> None:
    """Attempts to send a DM to the user and handles cases where DMs are closed."""
    try:
        await member.send(message)
    except discord.Forbidden:
        logger.warning(
            'Could not send DM to member, they might have DMs disabled.',
            name=member.name,
        )
