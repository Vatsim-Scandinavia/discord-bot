import discord
import datetime
import asyncio

from discord import app_commands
from discord.ext import commands, tasks

from helpers.config import config
from helpers.roles import Roles
from helpers.handler import Handler

class RolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.roles = Roles()
        self.handler = Handler()
        self.check_roles_loop.start()

    def cog_unload(self):
        self.check_roles_loop.cancel()

    async def check_roles(self, override: bool = False):
        await self.bot.wait_until_ready()

        if config.DEBUG and not override:
            print("check_roles skipped due to DEBUG ON. You can start manually with the command instead.", flush=True)
            return
        
        print(f"check_roles started at {datetime.datetime.now().isoformat()}", flush=True)

        guild = self.bot.get_guild(config.GUILD_ID)
        if guild is None:
            print(f"Guild with ID {config.GUILD_ID} not found.")
            return
        
        roles_data = await self.roles.get_roles()
        trainings_data = await self.roles.get_training()
        endorsement_data = await self.roles.get_endorsement()
        atc_activity_data = await self.roles.get_atc_activity()
        
        mentor_role = discord.utils.get(guild.roles, id=config.MENTOR_ROLE)
        training_staff_role = discord.utils.get(guild.roles, id=config.TRAINING_STAFF_ROLE)
        visitor_role = discord.utils.get(guild.roles, id=config.VISITOR_ROLE)
        
        for user in guild.members:
            await self.process_member_roles(user, mentor_role, training_staff_role, visitor_role, roles_data, trainings_data, endorsement_data, atc_activity_data)

        print(f"check_roles finished at {datetime.datetime.now().isoformat()}", flush=True)

    async def process_member_roles(self, user, mentor_role, training_staff_role, visitor_role, roles_data, trainings_data, endorsement_data, atc_activity_data):
        """
        Process and update member roles based on their API data.

        Args:
            user (discord.Member): The Discord member object.
            mentor_role (discord.Role): The Mentor role object.
            training_staff_role (discord.Role): The Training Staff role object.
            visitor_role (discord.Role): The Visitor role object.
            roles_data (list): The API response containing user roles.
            trainings_data (list): The API response containing user training data.
            endorsement_data (list): The API response containing user endorsement data.
            atc_activity_data (list): The API response containing ATC activity data.
        """
        try:
            cid = await self.handler.get_cid(user)
            if not cid:
                raise ValueError("No CID found in member's nickname.")

            should_be_mentor, should_be_training_staff, mentor_firs = self.get_mentor_roles(cid, roles_data)
            should_be_examiner, examiner_firs = self.get_examiner_roles(cid, endorsement_data)
            should_be_visitor = self.get_visitor_status(cid, endorsement_data)
            student_data, should_be_student = self.get_training_data_state(cid, trainings_data)

            tasks = [
                self.update_role(user, mentor_role, should_be_mentor, config.ROLE_REASONS["mentor_add"], config.ROLE_REASONS["mentor_remove"]),
                self.update_role(user, training_staff_role, should_be_training_staff, config.ROLE_REASONS["training_staff_add"], config.ROLE_REASONS["training_staff_remove"]),
                self.update_role(user, visitor_role, should_be_visitor, config.ROLE_REASONS["visitor_add"], config.ROLE_REASONS["visitor_remove"]),
                self.update_fir_roles(user, mentor_firs, "mentor", should_be_mentor),
                self.update_fir_roles(user, examiner_firs, "examiner", should_be_examiner),
                self.update_training_roles(user, student_data, should_be_student),
                self.update_fir_atc_roles(user, cid, atc_activity_data)
            ]

            await asyncio.gather(*tasks)

        except ValueError as e:
            print(f"ValueError for {user.name}: {e}", flush=True)
            if mentor_role in user.roles:
                await user.remove_roles(mentor_role, reason=config.ROLE_REASONS["no_cid"])
            if training_staff_role in user.roles:
                await user.remove_roles(training_staff_role, reason=config.ROLE_REASONS["no_cid"])
            if visitor_role in user.roles:
                await user.remove_roles(visitor_role, reason=config.ROLE_REASONS["no_cid"])
        
        except Exception as e:
            print(f"Error processing roles for {user.name}: {e}", flush=True)
        
        finally:
            if config.DEBUG:
                print(f"Finished processing roles for {user.name}.")


    def get_mentor_roles(self, cid, data):
        """
        Determine if the member is a mentor and/or training staff.

        Args:
            cid (int): The member's VATSIM CID.
            data (list): The API response data for roles.

        Returns:
            tuple: (should_be_mentor, should_be_training_staff, mentor_firs)
        """
        should_be_mentor = False
        should_be_training_staff = False
        mentor_firs = []

        for member_data in data:
            if member_data["id"] != cid:
                continue

            for fir, roles in member_data["roles"].items():
                if roles is None:
                    continue

                if "Mentor" in roles:
                    should_be_mentor = True
                    mentor_firs.append(fir)

                if "Moderator" in roles:
                    should_be_training_staff = True

        return should_be_mentor, should_be_training_staff, mentor_firs
    
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
            if member_data["id"]!= cid:
                continue

            endorsements = member_data.get("endorsements", {})
            examiner_endorsements = endorsements.get("examiner", [])

            if examiner_endorsements:
                should_be_examiner = True
                for endorsement in examiner_endorsements:
                    examiner_firs.extend(endorsement.get("areas", []))

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
            if member_data["id"] != cid:
                continue

            endorsements = member_data.get("endorsements", {})
            visitor_endorsements = endorsements.get("visiting", [])

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
            if member_data["id"] != cid:
                continue
            
            training = member_data.get("training", {})

            for item in training:
                if int(item["status"]) >= 2:
                    student_data[item["area"]] = item["ratings"]
                    should_be_student = True
        
        return student_data, should_be_student
    
    async def update_role(self, user, role, condition, add_reason, remove_reason):
        """
        Add or remove a role based on a condition.
        """
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
            role_type (str): The type of role to update ("mentor" or "examiner").
            should_be_assigned (bool): Whether the role should be assigned.
        """
        role_map = config.FIR_MENTORS if role_type == "mentor" else config.FIR_EXAMINERS
        add_reason = config.ROLE_REASONS[f"{role_type}_add"]
        remove_reason = config.ROLE_REASONS[f"{role_type}_remove"]

        for fir, role_id_str in role_map.items():
            role_id = int(role_id_str)

            fir_role = discord.utils.get(user.guild.roles, id=role_id)
            if not fir_role:
                print(f"Role with ID {role_id} not found in guild for FIR {fir}.")
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

                condition = area in student_data and rating in student_data[area] and should_be_student
                await self.update_role(user, training_role, condition, config.ROLE_REASONS["training_add"], config.ROLE_REASONS["training_remove"])

    async def update_fir_atc_roles(self, user, cid, atc_activity_data):
        """
        Update FIR-specific ATC roles based on activity and rating.
        """
        guild = user.guild
        role_tasks = []

        # Find user data
        user_entry = next((entry for entry in atc_activity_data if entry["id"] == cid), None)
        
        if not user_entry:
            # No ATC data available for the user → Remove any existing FIR roles
            for fir, role_id in config.CONTROLLER_FIR_ROLES.items():
                fir_role = discord.utils.get(guild.roles, id=int(role_id))
                if fir_role:
                    role_tasks.append(self.update_role(user, fir_role, False, "", f"Not active in {fir} (no data)"))

            for fir, roles in config.RATING_FIR_DATA.items():
                for role_id in roles.values():
                    fir_role = discord.utils.get(guild.roles, id=int(role_id))
                    if fir_role:
                        role_tasks.append(self.update_role(user, fir_role, False, "", f"Not active in {fir} (no data)"))

            await asyncio.gather(*role_tasks)
            return
        
        fir_activity = user_entry.get("atc_active_areas", {})
        rating = user_entry.get("rating", "")

        for fir, is_active in fir_activity.items():
            fir_cap = fir.capitalize()

            # Handle ATC rating-based roles
            fir_roles = config.RATING_FIR_DATA.get(fir_cap, {})
            role_id = fir_roles.get("C1") if rating in config.c1_equivalent_ratings else fir_roles.get(rating)
            if role_id:
                fir_role = discord.utils.get(guild.roles, id=int(role_id))
                if fir_role:
                    role_tasks.append(
                        self.update_role(user, fir_role, is_active, f"ATC active in {fir} as {rating}", f"Not ATC active in {fir}")
                    )

            # Handle general controller role
            controller_role_id = config.CONTROLLER_FIR_ROLES.get(fir_cap)
            if controller_role_id:
                controller_role = discord.utils.get(guild.roles, id=int(controller_role_id))
                if controller_role:
                    role_tasks.append(
                        self.update_role(user, controller_role, is_active, f"Active controller in {fir}", f"Not active controller in {fir}")
                    )

        await asyncio.gather(*role_tasks)
        

    @tasks.loop(seconds=config.CHECK_MEMBERS_INTERVAL)
    async def check_roles_loop(self):
        await self.check_roles()

    @app_commands.command(name="checkroles", description="Check and update roles manually.")
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def checkroles(self, interaction: discord.Interaction):
        await interaction.response.send_message("User roles refresh in progress...", ephemeral=True)
        await self.check_roles(override=True)
        await interaction.followup.send("User roles refresh process completed.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RolesCog(bot))