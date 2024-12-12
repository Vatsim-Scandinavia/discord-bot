import discord
import re
import datetime
import asyncio

from discord import app_commands
from discord.ext import commands, tasks

from helpers.config import config
from helpers.roles import Roles

class RolesCog(commands.Command):
    def __init__(self, bot):
        self.bot = bot
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
        
        roles_data = await Roles.get_roles(self)
        trainings_data = await Roles.get_training(self)
        examiner_data = await Roles.get_endorsement(self)
        
        mentor_role = discord.utils.get(guild.roles, id=config.MENTOR_ROLE)
        training_staff_role = discord.utils.get(guild.roles, id=config.TRAINING_STAFF_ROLE)
        visitor_role = discord.utils.get(guild.roles, id=config.VISITOR_ROLE)
        
        for user in guild.members:
            await self.process_member_roles(self, user, mentor_role, training_staff_role, visitor_role, roles_data, trainings_data, examiner_data)

        print(f"check_roles finished at {datetime.datetime.now().isoformat()}", flush=True)

    async def process_member_roles(self, user, mentor_role, training_staff_role, visitor_role, roles_data, trainings_data, examiner_data):
        """
        Process and update member roles based on their API data.

        Args:
            user (discord.Member): The Discord member object.
            mentor_role (discord.Role): The Mentor role object.
            training_staff_role (discord.Role): The Training Staff role object.
            visitor_role (discord.Role): The Visitor role object.
            roles_data (list): The API response containing user roles.
            trainings_data (list): The API response containing user training data.
            examiner_data (list): The API response containing user endorsement data.
        """
        try:
            cid = re.findall(r"\d+", str(user.nick))
            if not cid:
                raise ValueError("No CID found in member's nickname.")
            
            should_be_examiner, examiner_firs = self.get_member_roles_state(self, cid, examiner_data, "examiner")
            should_be_mentor, should_be_training_staff, mentor_firs = self.get_member_roles_state(self, cid, roles_data, "mentor")
            student_data, should_be_student = self.get_training_data_state(self, cid, trainings_data)

            valid_visitor = await Roles.get_endorsement(self)

            tasks = [
                self.update_role(self, user, mentor_role, should_be_mentor, config.ROLE_REASONS["mentor_add"], config.ROLE_REASONS["mentor_remove"]),
                self.update_role(self, user, training_staff_role, should_be_training_staff, config.ROLE_REASONS["training_staff_add"], config.ROLE_REASONS["training_staff_remove"]),
                self.update_role(self, user, visitor_role, valid_visitor, config.ROLE_REASONS["visitor_add"], config.ROLE_REASONS["visitor_remove"]),
                self.update_fir_roles(self, user, mentor_firs, "mentor", should_be_mentor),
                self.update_fir_roles(self, user, examiner_firs, "examiner", should_be_examiner),
                self.update_training_roles(self, user, student_data, should_be_student),
            ]

            await asyncio.gather(*tasks)

        except ValueError:
            if mentor_role in user.roles:
                await user.remove_roles(mentor_role, reason=config.ROLE_REASONS["no_cid"])
            if training_staff_role in user.roles:
                await user.remove_roles(training_staff_role, reason=config.ROLE_REASONS["no_cid"])
            if visitor_role in user.roles:
                await user.remove_roles(visitor_role, reason=config.ROLE_REASONS["no_cid"])
        except Exception as e:
            print(f"Error processing roles for {user.name}: {e}", flush=True)

    def get_member_roles_state(self, cid, data, type = None):
        """
        Determine the member's role states based on roles data.

        Args:
            cid (list): The member's VATSIM CID extracted from their nickname.
            data (dict): The API response data for roles or endorsements.
            type (str): Type of role to check (e.g., "examiner" or "mentor").

        Returns:
            tuple: Role state information based on the type.
        """
        if type == "mentor" and "roles" in data:
            should_be_mentor = False
            should_be_training_staff = False
            mentor_firs = []

            for fir, roles in data["roles"].items():
                if roles is None:
                    continue

                if "Mentor" in roles:
                    should_be_mentor = True
                    mentor_firs.append(fir)
                
                if "Moderator" in roles:
                    should_be_training_staff = True
                
                return should_be_mentor, should_be_training_staff, mentor_firs
        
        elif type == "examiner" and "endorsements" in data:
            if "examiner" in data["endorsements"] and data["endorsements"]["examiner"] is not None:
                should_be_examiner = False
                examiner_firs = []

                for endorsement in data["endorsements"]["examiner"]:
                    if int(data["cid"]) == int(cid[0]):
                        should_be_examiner = True
                        examiner_firs.extend(endorsement.get("areas", []))

            return should_be_examiner, examiner_firs
        
        return False, False, []
            
    
    def get_training_data_state(self, cid, trainings_data):
        """
        Determine the member's training roles based on training data.
        :return:
        """
        student_data = {}
        should_be_student = False

        for training in trainings_data:
            if int(training["id"]) == int(cid[0]):
                for item in training["training"]:
                    if int(item["status"]) >= 1:
                        student_data[item["area"]] = item["ratings"]
                        should_be_student = True
        
        return student_data, should_be_student
    
    async def update_role(self, user, role, condition, add_reason, remove_reason):
        """
        Add or remove a role based on a condition.
        :return:
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

        for fir in fir_data:
            role_id = role_map.get(fir)

            if not role_id:
                continue

            fir_role = discord.utils.get(user.guild.roles, id=role_id)

            await self.update_role(self, user, fir_role, should_be_assigned, add_reason, remove_reason)

    async def update_training_roles(self, user, student_data, should_be_student):
        """
        Update training roles for the member.
        :return:
        """
        for area, ratings in config.TRAINING_ROLES.items():
            for rating, role_id in ratings.items():
                training_role = discord.utils.get(user.guild.roles, id=role_id)
                if not training_role:
                    continue

                condition = area in student_data and rating in student_data[area] and should_be_student
                await self.update_role(self, user, training_role, condition, config.ROLE_REASONS["training_add"], config.ROLE_REASONS["training_remove"])

    @tasks.loop(seconds=config.CHECK_MEMBERS_INTERVAL)
    async def check_roles_loop(self):
        await self.check_roles()

    @app_commands.command(name="checkroles", description="Check and update roles manually.")
    @app_commands.checks.has_any_role(*config.STAFF_ROLES)
    async def checkroles(self, interaction: discord.Interaction):
        await interaction.response.send_message("User roles refresh in progress...", ephemeral=True)
        await self.check_roles(override=True)
        await interaction.followup.send("User roles refresh process completed.", ephemeral=True)
