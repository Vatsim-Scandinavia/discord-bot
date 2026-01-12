import asyncio
import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import discord
import emoji
import structlog
from discord import app_commands
from discord.ext import commands, tasks

from core.exceptions import GuildNotFound
from helpers.config import config
from helpers.handler import Handler
from helpers.roles import Roles

logger = structlog.stdlib.get_logger()


@dataclass
class MentorBuddyInfo:
    """Data structure for mentor and buddy role information."""

    mentor_should_be: bool
    mentor_firs: list[str]
    buddy_should_be: bool
    buddy_firs: list[str]
    training_staff_should_be: bool


# We don't instantiate these, but we need to import them for type checking
if TYPE_CHECKING:
    from collections.abc import Coroutine

    from cogs.coordination import CoordinationCog


class RolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.roles = Roles()
        self.handler = Handler()
        self.check_roles_loop.start()

    async def cog_unload(self):
        self.check_roles_loop.cancel()

    async def check_roles(self, override: bool = False):
        await self.bot.wait_until_ready()

        if config.DEBUG and not override:
            logger.info(
                'Job skipped due to DEBUG mode. You can start the job with the command.',
                job='check_roles',
                status='skipped',
            )
            return

        logger.info(
            'Job started',
            job='check_roles',
            start_time=datetime.datetime.now().isoformat(),
            status='start',
        )

        guild = self.bot.get_guild(config.GUILD_ID)
        if guild is None:
            logger.critical('Guild not found', guild_id=config.GUILD_ID)
            return

        roles_data = await self.roles.get_roles()
        trainings_data = await self.roles.get_training()
        endorsement_data = await self.roles.get_endorsement()
        atc_activity_data = await self.roles.get_atc_activity()

        mentor_role = discord.utils.get(guild.roles, id=config.MENTOR_ROLE)
        buddy_role = discord.utils.get(guild.roles, id=config.BUDDY_ROLE)
        training_staff_role = discord.utils.get(
            guild.roles, id=config.TRAINING_STAFF_ROLE
        )
        visitor_role = discord.utils.get(guild.roles, id=config.VISITOR_ROLE)

        for user in guild.members:
            await self.process_member_roles(
                user,
                mentor_role,
                buddy_role,
                training_staff_role,
                visitor_role,
                roles_data,
                trainings_data,
                endorsement_data,
                atc_activity_data,
            )

        logger.info(
            'Job finished',
            job='check_roles',
            end_time=datetime.datetime.now().isoformat(),
            status='success',
        )

    async def process_member_roles(
        self,
        user,
        mentor_role,
        buddy_role,
        training_staff_role,
        visitor_role,
        roles_data,
        trainings_data,
        endorsement_data,
        atc_activity_data,
    ):
        """
        Process and update member roles based on their API data.

        Args:
            user (discord.Member): The Discord member object.
            mentor_role (discord.Role): The Mentor role object.
            buddy_role (discord.Role): The Buddy role object.
            training_staff_role (discord.Role): The Training Staff role object.
            visitor_role (discord.Role): The Visitor role object.
            roles_data (list): The API response containing user roles.
            trainings_data (list): The API response containing user training data.
            endorsement_data (list): The API response containing user endorsement data.
            atc_activity_data (list): The API response containing ATC activity data.

        """
        try:
            cid = self.handler.get_cid(user)
            if not cid:
                raise ValueError("No CID found in member's nickname.")

            mentor_buddy_info = self.get_mentor_roles(cid, roles_data)
            should_be_examiner, examiner_firs = self.get_examiner_roles(
                cid, endorsement_data
            )
            should_be_visitor = self.get_visitor_status(cid, endorsement_data)
            student_data, should_be_student = self.get_training_data_state(
                cid, trainings_data
            )

            tasks = [
                self.update_role(
                    user,
                    mentor_role,
                    mentor_buddy_info.mentor_should_be,
                    config.ROLE_REASONS['mentor_add'],
                    config.ROLE_REASONS['mentor_remove'],
                ),
                self.update_role(
                    user,
                    buddy_role,
                    mentor_buddy_info.buddy_should_be,
                    config.ROLE_REASONS['buddy_add'],
                    config.ROLE_REASONS['buddy_remove'],
                ),
                self.update_role(
                    user,
                    training_staff_role,
                    mentor_buddy_info.training_staff_should_be,
                    config.ROLE_REASONS['training_staff_add'],
                    config.ROLE_REASONS['training_staff_remove'],
                ),
                self.update_role(
                    user,
                    visitor_role,
                    should_be_visitor,
                    config.ROLE_REASONS['visitor_add'],
                    config.ROLE_REASONS['visitor_remove'],
                ),
                self.update_fir_roles(
                    user,
                    mentor_buddy_info.mentor_firs,
                    'mentor',
                    mentor_buddy_info.mentor_should_be,
                ),
                self.update_fir_roles(
                    user,
                    mentor_buddy_info.buddy_firs,
                    'buddy',
                    mentor_buddy_info.buddy_should_be,
                ),
                self.update_fir_roles(
                    user, examiner_firs, 'examiner', should_be_examiner
                ),
                self.update_training_roles(user, student_data, should_be_student),
                self.update_fir_atc_roles(user, cid, atc_activity_data),
            ]

            await asyncio.gather(*tasks)

        except ValueError as e:
            logger.warning(
                'Failed to process roles, probably because we could not get CID due ValueError: will remove any roles',
                name=user.name,
                nick=user.nick,
                error=e,
            )
            if mentor_role in user.roles:
                await user.remove_roles(
                    mentor_role, reason=config.ROLE_REASONS['no_cid']
                )
            if buddy_role in user.roles:
                await user.remove_roles(
                    buddy_role, reason=config.ROLE_REASONS['no_cid']
                )
            if training_staff_role in user.roles:
                await user.remove_roles(
                    training_staff_role, reason=config.ROLE_REASONS['no_cid']
                )
            if visitor_role in user.roles:
                await user.remove_roles(
                    visitor_role, reason=config.ROLE_REASONS['no_cid']
                )

        except Exception:
            logger.exception('Error processing roles', name=user.name, nick=user.nick)

        finally:
            # TODO(thor): Replace if-check with correctly configured logger with level filtering
            # TODO(thor): Configure structlog to output module location (e.g. cogs.roles)
            if config.DEBUG:
                logger.debug('Finished processing roles', name=user.name)

    def get_mentor_roles(self, cid, data):
        """
        Determine if the member is a mentor, buddy, and/or training staff.

        Args:
            cid (int): The member's VATSIM CID.
            data (list): The API response data for roles.

        Returns:
            MentorBuddyInfo: A data structure containing mentor, buddy, and training staff information.

        """
        should_be_mentor = False
        should_be_training_staff = False
        should_be_buddy = False
        mentor_firs = []
        buddy_firs = []

        for member_data in data:
            if member_data['id'] != cid:
                continue

            for fir, roles in member_data['roles'].items():
                if roles is None:
                    continue

                if 'Mentor' in roles:
                    should_be_mentor = True
                    mentor_firs.append(fir)

                if 'Buddy' in roles:
                    should_be_buddy = True
                    buddy_firs.append(fir)

                if 'Moderator' in roles:
                    should_be_training_staff = True

        return MentorBuddyInfo(
            mentor_should_be=should_be_mentor,
            mentor_firs=mentor_firs,
            buddy_should_be=should_be_buddy,
            buddy_firs=buddy_firs,
            training_staff_should_be=should_be_training_staff,
        )

    def get_examiner_roles(self, cid, data):
        """
        Determine if the member is an examiner.

        Args:
            cid (int): The member's VATSIM CID.
            data (list): The API response data for endorsements.

        Returns:
            tuple: (should_be_examiner, None, examiner_firs)

        """
        should_be_examiner = False
        examiner_firs = []

        for member_data in data:
            if member_data['id'] != cid:
                continue

            endorsements = member_data.get('endorsements', {})
            examiner_endorsements = endorsements.get('examiner', [])

            if examiner_endorsements:
                should_be_examiner = True
                for endorsement in examiner_endorsements:
                    examiner_firs.extend(endorsement.get('areas', []))

        return should_be_examiner, examiner_firs

    def get_visitor_status(self, cid, data):
        """
        Determine if a user should have the Visitor role based on endorsement data.

        Args:
            cid (int): The user's VATSIM CID.
            data (list): The API response containing user endorsement data.

        Returns:
            bool: Whether the user qualifies for the Visitor role.

        """
        should_be_visitor = False

        for member_data in data:
            if member_data['id'] != cid:
                continue

            endorsements = member_data.get('endorsements', {})
            visitor_endorsements = endorsements.get('visiting', [])

            if visitor_endorsements:
                should_be_visitor = True
                break

        return should_be_visitor

    def get_training_data_state(self, cid, trainings_data):
        """
        Determine the member's training roles based on training data.
        :return:
        """
        student_data = {}
        should_be_student = False

        for member_data in trainings_data:
            if member_data['id'] != cid:
                continue

            training = member_data.get('training', {})

            for item in training:
                if int(item['status']) >= 2:
                    student_data[item['area']] = item['ratings']
                    should_be_student = True

        return student_data, should_be_student

    async def update_role(self, user, role, condition, add_reason, remove_reason):
        """Add or remove a role based on a condition."""
        if condition and role not in user.roles:
            await user.add_roles(role, reason=add_reason)
        elif not condition and role in user.roles:
            await user.remove_roles(role, reason=remove_reason)

    async def update_fir_roles(self, user, fir_data, role_type, should_be_assigned):
        """
        Update FIR-specific roles for the member.

        Args:
            user (discord.Member): The Discord member object.
            fir_data (list): A list of FIRs the user is assigned to.
            role_type (str): The type of role to update ("mentor", "buddy", or "examiner").
            should_be_assigned (bool): Whether the role should be assigned.

        """
        ROLE_FIR_MAP = {
            'mentor': config.FIR_MENTORS,
            'buddy': config.FIR_BUDDIES,
            'examiner': config.FIR_EXAMINERS,
        }
        role_map = ROLE_FIR_MAP[role_type]
        add_reason = config.ROLE_REASONS[f'{role_type}_add']
        remove_reason = config.ROLE_REASONS[f'{role_type}_remove']

        for fir, role_id_str in role_map.items():
            role_id = int(role_id_str)

            fir_role = discord.utils.get(user.guild.roles, id=role_id)
            if not fir_role:
                logger.warning('Role not found in FIR.', role_id=role_id, fir=fir)
                continue

            if fir in fir_data and should_be_assigned:
                await self.update_role(user, fir_role, True, add_reason, remove_reason)

            elif fir not in fir_data and not should_be_assigned:
                await self.update_role(user, fir_role, False, add_reason, remove_reason)

    async def update_training_roles(self, user, student_data, should_be_student):
        """
        Update training roles for the member.
        :return:
        """
        for area, ratings in config.TRAINING_ROLES.items():
            for rating, role_id in ratings.items():
                training_role = discord.utils.get(user.guild.roles, id=int(role_id))
                if not training_role:
                    continue

                condition = (
                    area in student_data
                    and rating in student_data[area]
                    and should_be_student
                )
                await self.update_role(
                    user,
                    training_role,
                    condition,
                    config.ROLE_REASONS['training_add'],
                    config.ROLE_REASONS['training_remove'],
                )

    async def update_fir_atc_roles(self, user, cid, atc_activity_data):
        """Update FIR-specific ATC roles based on activity and rating."""
        guild = user.guild
        role_tasks = []

        # Find user data
        user_entry = next(
            (entry for entry in atc_activity_data if entry['id'] == cid), None
        )

        if not user_entry:
            # No ATC data available for the user → Remove any existing FIR roles
            for fir, role_id in config.CONTROLLER_FIR_ROLES.items():
                fir_role = discord.utils.get(guild.roles, id=int(role_id))
                if fir_role:
                    role_tasks.append(
                        self.update_role(
                            user, fir_role, False, '', f'Not active in {fir} (no data)'
                        )
                    )

            for fir, roles in config.RATING_FIR_DATA.items():
                for role_id in roles.values():
                    fir_role = discord.utils.get(guild.roles, id=int(role_id))
                    if fir_role:
                        role_tasks.append(
                            self.update_role(
                                user,
                                fir_role,
                                False,
                                '',
                                f'Not active in {fir} (no data)',
                            )
                        )

            await asyncio.gather(*role_tasks)
            return

        fir_activity = user_entry.get('atc_active_areas', {})
        rating = user_entry.get('rating', '')

        for fir, is_active in fir_activity.items():
            fir_cap = fir.capitalize()

            # Handle ATC rating-based roles
            fir_roles = config.RATING_FIR_DATA.get(fir_cap, {})
            role_id = (
                fir_roles.get('C1')
                if rating in config.c1_equivalent_ratings
                else fir_roles.get(rating)
            )
            if role_id:
                fir_role = discord.utils.get(guild.roles, id=int(role_id))
                if fir_role:
                    role_tasks.append(
                        self.update_role(
                            user,
                            fir_role,
                            is_active,
                            f'ATC active in {fir} as {rating}',
                            f'Not ATC active in {fir}',
                        )
                    )

            # Handle general controller role
            controller_role_id = config.CONTROLLER_FIR_ROLES.get(fir_cap)
            if controller_role_id:
                controller_role = discord.utils.get(
                    guild.roles, id=int(controller_role_id)
                )
                if controller_role:
                    role_tasks.append(
                        self.update_role(
                            user,
                            controller_role,
                            is_active,
                            f'Active controller in {fir}',
                            f'Not active controller in {fir}',
                        )
                    )

        await asyncio.gather(*role_tasks)

    async def _handle_role_reaction(
        self, payload: discord.RawReactionActionEvent, action: Literal['add', 'remove']
    ):
        """Handles changing roles based on reactions."""
        if not payload.guild_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            raise GuildNotFound(payload.guild_id, payload)

        user = guild.get_member(payload.user_id)
        if not user:
            return

        emoji_name = emoji.demojize(payload.emoji.name)
        message_id = str(payload.message_id)

        if (
            message_id not in config.REACTION_MESSAGE_IDS
            or emoji_name not in config.REACTION_ROLES
        ):
            return

        role_id = int(config.REACTION_ROLES[emoji_name])
        role = discord.utils.get(guild.roles, id=role_id)

        if action == 'add' and role and role not in user.roles:
            await user.add_roles(role, reason=config.ROLE_REASONS['reaction_add'])
            await self._send_dm(
                user,
                f'You have been given the `{role.name}` role because you reacted with {payload.emoji}',
            )

        if action == 'remove' and role and role in user.roles:
            await user.remove_roles(role, reason=config.ROLE_REASONS['reaction_remove'])
            await self._send_dm(
                user,
                f'You no longer have the `{role.name}` role because you removed your reaction.',
            )

    async def _send_dm(self, member: discord.Member, message: str):
        """Attempts to send a DM to the user and handles cases where DMs are closed."""
        try:
            await member.send(message)
        except discord.Forbidden:
            logger.warning(
                'Could not send DM to member, they might have DMs disabled.',
                name=member.name,
            )

    @tasks.loop(seconds=config.CHECK_MEMBERS_INTERVAL)
    async def check_roles_loop(self):
        await self.check_roles()

    @app_commands.command(
        name='checkroles', description='Check and update roles manually.'
    )
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def checkroles(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            'User roles refresh in progress...', ephemeral=True
        )
        await self.check_roles(override=True)
        await interaction.followup.send(
            'User roles refresh process completed.', ephemeral=True
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Listen to member updates and assigns role according to the nick.

        We listen to member update events to catch changes made by the VATSIM Community bot.
        One alternative approach include listening to the audit log.

        Todo:
            This entire function should possibly be merged with the cogs.tasks.check_members routine.

        """
        if before.nick == after.nick:
            return

        coordination: CoordinationCog | None = self.bot.get_cog('CoordinationCog')  # pyright: ignore[reportAssignmentType]
        if not coordination:
            logger.warning(
                'Could not get the coordination cog; cannot check for modified nicknames.',
                user=after.name,
                nick=after.nick,
            )

        # NOTE: While this should prevent the bot from assigning roles while a member has
        # a modified (i.e. position-prefixed station) nickname, it doesn't prevent any
        # race condition from occuring *during* the user's state change (i.e. when moving
        # between or leaving voice channels).
        if coordination and await coordination.has_modified_nick(after):
            logger.info(
                'User has modified nick: skipping role assignment.',
                user=after.name,
                nick=after.nick,
            )
            return

        # Define role objects
        vatsca_member = discord.utils.get(
            after.guild.roles, id=config.VATSCA_MEMBER_ROLE
        )
        vatsim_member = discord.utils.get(
            after.guild.roles, id=config.VATSIM_MEMBER_ROLE
        )

        if not vatsca_member or not vatsim_member:
            # TODO(thor): Replace with a custom exception (which probably belongs in the core module)
            logger.error(
                'The (sub-)division or VATSIM role was not found in the guild.',
                division=config.VATSCA_MEMBER_ROLE,
                vatsim=config.VATSIM_MEMBER_ROLE,
            )
            return

        # Extract cid from nickname, exit early if not found
        cid = self.handler.get_cid(after)

        try:
            api_data = await self.handler.get_division_members()

            should_have_vatsca = any(
                int(entry['id']) == cid
                and str(entry['subdivision']) == str(config.VATSIM_SUBDIVISION)
                for entry in api_data
            )
            logger.info('Fetched division members from API', len=len(api_data))

            # Manage role assignments
            tasks: list[Coroutine[Any, Any, None]] = []

            if vatsim_member in after.roles:
                # add VATSCA if required otherwise remove it
                if should_have_vatsca and vatsca_member not in after.roles:
                    tasks.append(
                        after.add_roles(
                            vatsca_member, reason='Missing role in on_member_update'
                        )
                    )
                elif not should_have_vatsca and vatsca_member in after.roles:
                    tasks.append(
                        after.remove_roles(
                            vatsca_member, reason='Redundant role in on_member_update'
                        )
                    )

            elif vatsca_member in after.roles:
                # Remove VATSCA if the user doesn't have VATSIM role
                tasks.append(
                    after.remove_roles(
                        vatsca_member,
                        reason='Redunant role because VATSIM role is missing in on_member_update',
                    )
                )

            if tasks:
                await asyncio.gather(*tasks)

        # TODO(thor): Replace with either custom exceptions or find out how to move them out to the core handler
        except discord.Forbidden as e:
            logger.exception('Bot lacks permission for action', error=e)

        except discord.HTTPException as e:
            logger.exception('HTTP error', error=e)

        except Exception as e:
            logger.exception('Unexpected error', error=e)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Event listener for adding roles based on reactions."""
        if self.bot.user and payload.user_id == self.bot.user.id:
            return
        await self._handle_role_reaction(payload, 'add')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Event listener for removing roles based on reactions."""
        if self.bot.user and payload.user_id == self.bot.user.id:
            return
        await self._handle_role_reaction(payload, 'remove')


async def setup(bot: commands.Bot):
    await bot.add_cog(RolesCog(bot))
