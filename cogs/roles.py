import discord
import re
import datetime

from discord import app_commands
from discord.ext import commands, tasks
from helpers.config import (
    CHECK_MENTORS_INTERVAL, DEBUG, GUILD_ID, MENTOR_ROLE,
    ROLE_REASONS, FIR_MENTORS, TRAINING_STAFF_ROLE, TRAINING_ROLES
)
from helpers.roles import Roles
from helpers.message import staff_roles
from helpers.handler import Handler

class RolesCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_roles_loop.start()
    
    def cog_unload(self):
        self.check_roles_loop.cancel()

    
    async def check_roles(self, override=False):
        """
        Check roles for mentors, training staff and etc.
        """
        await self.bot.wait_until_ready()

        if DEBUG and not override:
            print("check_roles skipped due to DEBUG ON. You can start manually with command instead.", flush=True)
            return
            
        print(f"check_roles started at {str(datetime.datetime.now().isoformat())}", flush=True)

        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            print(f"Guild with ID {GUILD_ID} not found", flush=True)

        mentor_role = discord.utils.get(guild.roles, id=MENTOR_ROLE)
        training_staff_role = discord.utils.get(guild.roles, id=TRAINING_STAFF_ROLE)

        roles = await Roles.get_roles(self)
        trainings = await Roles.get_training(self)

        for user in guild.members:            
            try:
                user_cid = re.findall(r'\d+', str(user.nick)) or [None]
                cid = int(user_cid[0]) if user_cid[0] else None
                if not cid:
                    raise ValueError("No CID found in nickname.")

                # Role assignment conditions
                should_be_mentor, should_be_training_staff, belong_to = False, False, []

                for role in roles:
                    if cid == int(role['id']):
                        if 'Mentor' in role['roles'].values():
                            should_be_mentor = True
                            belong_to.extend(role['roles'].keys())
                        if 'Moderator' in role['roles'].values():
                            should_be_training_staff = True


                student_data, should_be_student = {}, False

                for training in trainings:
                    if cid == int(training["training"]):
                        for item in training["training"]:
                            if int(item['status']) >= 1:
                                student_data[item['area']] = item['ratings']
                                should_be_student = True
                        
                        
                await self.update_user_roles(
                    user, mentor_role, training_staff_role, belong_to, student_data,
                    should_be_mentor, should_be_training_staff, should_be_student
                )

            except ValueError as e:
                if mentor_role in user.roles:
                    await user.remove_roles(mentor_role, reason=ROLE_REASONS['no_cid'])
                    
            except Exception as e:
                print(e, flush=True)
                continue

        print("check_roles finished at " + str(datetime.datetime.now().isoformat()), flush=True)

    async def update_user_roles(self, user, mentor_role, training_staff_role, belong_to, student_data, 
                                should_be_mentor, should_be_training_staff, should_be_student):
        """
        Update roles for a user
        """
        if should_be_mentor:
            if mentor_role not in user.roles:
                await user.add_roles(mentor_role, reason=ROLE_REASONS['mentor_add'])
        else:
            if mentor_role in user.roles:
                await user.remove_roles(mentor_role, reason=ROLE_REASONS['mentor_remove'])

        if should_be_training_staff:
            if training_staff_role not in user.roles:
                await user.add_roles(training_staff_role, reason=ROLE_REASONS['training_staff_add'])
            else:
                await user.remove_roles(training_staff_role, reason=ROLE_REASONS['training_staff_remove'])

        # Update FIR Mentors
        for fir, role_id in FIR_MENTORS.items():
            fir_role = discord.utils.get(user.guild.roles, id=role_id)
            
            if fir in belong_to and should_be_mentor and fir_role not in user.roles:
                await user.add_roles(fir_role, reason=ROLE_REASONS['mentor_add'])
            elif fir not in belong_to and fir_role in user.roles:
                await user.remove_roles(fir_role, reason=ROLE_REASONS['mentor_remove'])
                                        
        for area, roles_dict in TRAINING_ROLES.items():
            for rating, role_id in roles_dict.items():
                training_role = discord.utils.get(user.guild.roles, id=role_id)

                if area in student_data and rating in student_data[area]:
                    if training_role not in user.roles:
                        await user.add_roles(training_role, reason=ROLE_REASONS['training_add'])
                else:
                    if training_role in user.roles:
                        await user.remove_roles(training_role, reason=ROLE_REASONS['training_remove'])

    @tasks.loop(seconds=CHECK_MENTORS_INTERVAL)
    async def check_roles_loop(self):
        await self.check_roles()

    @app_commands.command(name="checkroles", description="Check mentor & training staff roles")
    @app_commands.checks.has_any_role(*staff_roles())
    async def check_mentors_command(self, interaction: discord.Integration):
        ctx = Handler.get_context(self.bot, interaction)

        await ctx.send("Staff refresh in progress")
        await self.check_roles(True)
        await ctx.send("Staff refresh process finished")

async def setup(bot):
    await bot.add_cog(RolesCog(bot))

