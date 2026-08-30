import asyncio
import datetime
from dataclasses import dataclass

import discord
import structlog
from discord import app_commands
from discord.ext import commands, tasks

from core.roles import cleanup_membership_roles, update_role
from helpers.config import config
from helpers.handler import Handler
from helpers.roles import Roles

logger = structlog.stdlib.get_logger()
ALREADY_PRINTED_DEBUG_MESSAGE = set()


@dataclass
class MentorBuddyInfo:
    """Data structure for mentor and buddy role information."""

    mentor_should_be: bool
    mentor_firs: list[str]
    buddy_should_be: bool
    buddy_firs: list[str]
    training_staff_should_be: bool


class CCRolesCog(commands.Cog):
    """Syncs Discord roles from the Control Center training system."""

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
            if 'check_roles' not in ALREADY_PRINTED_DEBUG_MESSAGE:
                ALREADY_PRINTED_DEBUG_MESSAGE.add('check_roles')
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

        # Every check below reads "not in the Control Center data" as "should not
        # have the role". If a fetch failed or came back empty we would therefore
        # strip the managed roles from the whole guild, so stop instead.
        missing = self.missing_cc_datasets(
            {
                'roles': roles_data,
                'training': trainings_data,
                'endorsements': endorsement_data,
                'atc_activity': atc_activity_data,
            }
        )
        if missing:
            logger.error(
                'Job aborted, Control Center returned no data',
                job='check_roles',
                status='aborted',
                missing=missing,
            )
            return

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

    @staticmethod
    def missing_cc_datasets(datasets: dict[str, list | None]) -> list[str]:
        """
        Name the Control Center datasets that came back unusable.

        A ``None`` value is a failed fetch and an empty list is a successful but
        empty response. Both are unsafe to act on, so both are reported.

        Args:
            datasets (dict): Dataset name mapped to the fetched API data.

        Returns:
            list[str]: The names of the datasets holding no data.

        """
        return [name for name, data in datasets.items() if not data]

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
            # Check if the user has the VATSIM member role, if not clear all managed roles and skip.
            cid = self.handler.get_cid(user)
            if cid is None:
                await cleanup_membership_roles(
                    user, config.ROLE_REASONS['no_cid'], include_vatsca=True
                )
                return

            mentor_buddy_info = self.get_mentor_roles(cid, roles_data)
            should_be_examiner, examiner_firs = self.get_examiner_roles(
                cid, endorsement_data
            )
            should_be_visitor = self.get_visitor_status(cid, endorsement_data)
            student_data, should_be_student = self.get_training_data_state(
                cid, trainings_data
            )

            tasks = [
                update_role(
                    user,
                    mentor_role,
                    mentor_buddy_info.mentor_should_be,
                    config.ROLE_REASONS['mentor_add'],
                    config.ROLE_REASONS['mentor_remove'],
                ),
                update_role(
                    user,
                    buddy_role,
                    mentor_buddy_info.buddy_should_be,
                    config.ROLE_REASONS['buddy_add'],
                    config.ROLE_REASONS['buddy_remove'],
                ),
                update_role(
                    user,
                    training_staff_role,
                    mentor_buddy_info.training_staff_should_be,
                    config.ROLE_REASONS['training_staff_add'],
                    config.ROLE_REASONS['training_staff_remove'],
                ),
                update_role(
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
                'Stopped to process memeber role due to being unable to extract CID; cleaning managed roles.',
                name=user.name,
                nick=user.nick,
                error=e,
            )
            await cleanup_membership_roles(
                user, config.ROLE_REASONS['unknown_cid'], include_vatsca=True
            )

        except Exception:
            logger.exception('Error processing roles', name=user.name, nick=user.nick)

        finally:
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

                # Control Center returns lowercase role identifiers (e.g. 'mentor');
                # normalise so matching is resilient to casing changes on the API side.
                normalised_roles = {role.lower() for role in roles}

                # The CC identifiers that map to each Discord role are configurable
                # and may list several values, so a non-empty intersection means at
                # least one configured identifier matched for this FIR.
                if normalised_roles & config.CC_MENTOR_ROLES:
                    should_be_mentor = True
                    mentor_firs.append(fir)

                if normalised_roles & config.CC_BUDDY_ROLES:
                    should_be_buddy = True
                    buddy_firs.append(fir)

                if normalised_roles & config.CC_TRAINING_ROLES:
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

            # The member keeps the role only while they hold the parent role and
            # are still listed for this FIR. Anything else means remove it, so a
            # member who moves between FIRs does not keep the old one.
            condition = should_be_assigned and fir in fir_data
            await update_role(user, fir_role, condition, add_reason, remove_reason)

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
                await update_role(
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
                        update_role(
                            user, fir_role, False, '', f'Not active in {fir} (no data)'
                        )
                    )

            for fir, roles in config.RATING_FIR_DATA.items():
                for role_id in roles.values():
                    fir_role = discord.utils.get(guild.roles, id=int(role_id))
                    if fir_role:
                        role_tasks.append(
                            update_role(
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
                        update_role(
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
                        update_role(
                            user,
                            controller_role,
                            is_active,
                            f'Active controller in {fir}',
                            f'Not active controller in {fir}',
                        )
                    )

        await asyncio.gather(*role_tasks)

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


async def setup(bot: commands.Bot):
    await bot.add_cog(CCRolesCog(bot))
