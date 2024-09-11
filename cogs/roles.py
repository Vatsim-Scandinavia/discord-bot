import discord
import re

from discord import app_commands
from discord.ext import commands, tasks
import datetime
from helpers.config import CHECK_MENTORS_INTERVAL, DEBUG, GUILD_ID, MENTOR_ROLE, ROLE_REASONS, FIR_MENTORS, TRAINING_STAFF_ROLE, TRAINING_ROLES
from helpers.roles import Roles
from helpers.message import staff_roles

class RolesCog(commands.Cog):

    MENTOR_ROLE_ADD_REASON = ROLE_REASONS['mentor_add']
    MENTOR_ROLE_REMOVE_REASON = ROLE_REASONS['mentor_remove']
    TRAINING_STAFF_ADD_REASON = ROLE_REASONS['training_staff_add']
    TRAINING_STAFF_REMOVE_REASON = ROLE_REASONS['training_staff_remove']
    STUDENT_TRAINING_ADD_REASON = ROLE_REASONS['training_add']
    STUDENT_TRAINING_REMOVE_REASON = ROLE_REASONS['training_remove']
    NO_CID_REMOVE_REASON = ROLE_REASONS['no_cid']
    NO_AUTH_REMOVE_REASON = ROLE_REASONS['no_auth']

    GUILD_ID = [GUILD_ID]
    
    def __init__(self, bot):
        self.bot = bot
        self.check_roles_loop.start()
    
    def cog_unload(self):
        self.check_roles_loop.cancel()

    
    async def check_roles(self, override=False):
        await self.bot.wait_until_ready()
        if DEBUG == True and override == False:
            print("check_roles skipped due to DEBUG ON. You can start manually with command instead.", flush=True)
            return
            
        print("check_roles started at " + str(datetime.datetime.now().isoformat()), flush=True)

        guild = self.bot.get_guild(GUILD_ID)
        users = guild.members

        mentor_role = discord.utils.get(guild.roles, id=MENTOR_ROLE)

        training_staff_role = discord.utils.get(guild.roles, id=TRAINING_STAFF_ROLE)

        mentors = await Roles.get_mentors(self)

        moderators = await Roles.get_moderators(self)

        trainings = await Roles.get_training(self)

        for user in users:            
            try:
                cid = re.findall(r'\d+', str(user.nick))

                if len(cid) < 1:
                    raise ValueError

                should_be_mentor = False

                belong_to = []

                for mentor in mentors:
                    if int(mentor['id']) == int(cid[0]):
                        should_be_mentor = True
                        for fir in mentor['fir']:
                            belong_to.append(fir)

                should_be_training_staff = False            
                
                for moderator in moderators:
                    if int(moderator['id']) == int(cid[0]):
                        should_be_training_staff = True

                student_data = {}
                should_be_student = False

                for training in trainings:
                    if int(training['id']) == int(cid[0]):
                        for item in training["training"]:
                            if int(item['status']) >= 1:
                                student_data[item['area']] = item['ratings']
                                should_be_student = True
                        
                        

                if mentor_role not in user.roles and should_be_mentor == True:
                    await user.add_roles(mentor_role, reason=self.MENTOR_ROLE_ADD_REASON)
                elif mentor_role in user.roles and should_be_mentor == False:
                    await user.remove_roles(mentor_role, reason=self.MENTOR_ROLE_REMOVE_REASON)

                if training_staff_role not in user.roles and should_be_training_staff == True:
                    await user.add_roles(training_staff_role, reason=self.TRAINING_STAFF_ADD_REASON)
                elif training_staff_role in user.roles and should_be_training_staff == False:
                    await user.remove_roles(training_staff_role, reason=self.TRAINING_STAFF_REMOVE_REASON)

                for fir in FIR_MENTORS:
                    FIR_ROLE = discord.utils.get(guild.roles, id=int(FIR_MENTORS[fir]))
                    if FIR_ROLE not in user.roles and fir in belong_to and should_be_mentor == True:
                        await user.add_roles(FIR_ROLE, reason=self.MENTOR_ROLE_ADD_REASON)
                    elif FIR_ROLE in user.roles and fir not in belong_to and should_be_mentor == False:
                        await user.remove_roles(FIR_ROLE, reason=self.MENTOR_ROLE_REMOVE_REASON)

                for entry in TRAINING_ROLES:
                    for item in TRAINING_ROLES[entry]:
                        training_role = discord.utils.get(guild.roles, id=int(TRAINING_ROLES[entry][item]))
                        if entry in student_data.keys():
                            if training_role not in user.roles and item in student_data[entry] and should_be_student:
                                await user.add_roles(training_role, reason=self.STUDENT_TRAINING_ADD_REASON)
                            elif training_role in user.roles and item not in student_data[entry]:
                                await user.remove_roles(training_role, reason=self.STUDENT_TRAINING_REMOVE_REASON)

                        elif training_role in user.roles:
                            await user.remove_roles(training_role, reason=self.STUDENT_TRAINING_REMOVE_REASON)

            except ValueError as e:
                if mentor_role in user.roles:
                    await user.remove_roles(mentor_role, reason=self.NO_CID_REMOVE_REASON)
                    
            except Exception as e:
                print(e, flush=True)
                continue

        print("check_roles finished at " + str(datetime.datetime.now().isoformat()), flush=True)

    @tasks.loop(seconds=CHECK_MENTORS_INTERVAL)
    async def check_roles_loop(self):
        await self.check_roles()

    @app_commands.command(name="checkroles", description="Check mentor & training staff roles")
    @app_commands.checks.has_any_role(*staff_roles())
    async def check_mentors_command(self, interaction: discord.Integration):
        ctx: commands.Context = await self.bot.get_context(interaction)
        interaction._baton = ctx

        await ctx.send("Staff refresh in progress")
        await self.check_roles(True)
        await ctx.send("Staff refresh process finished")

async def setup(bot):
    await bot.add_cog(RolesCog(bot))

