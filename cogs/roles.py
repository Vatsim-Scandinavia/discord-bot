import discord
import re

from discord.ext import commands, tasks
from discord_slash import cog_ext
import datetime
from helpers.config import CHECK_MENTORS_INTERVAL, DEBUG, GUILD_ID, MENTOR_ROLE, ROLE_REASONS, FIR_MENTORS, TRAINING_STAFF_ROLE
from helpers.roles import Roles
from helpers.message import staff_roles

class RolesCog(commands.Cog):

    MENTOR_ROLE_ADD_REASON = ROLE_REASONS['mentor_add']
    MENTOR_ROLE_REMOVE_REASON = ROLE_REASONS['mentor_remove']
    TRAINING_STAFF_ADD_REASON = ROLE_REASONS['training_staff_add']
    TRAINING_STAFF_REMOVE_REASON = ROLE_REASONS['training_staff_remove']
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
            print("check_roles skipped due to DEBUG ON. You can start manually with command instead.")
            return
            
        print("check_roles started at " + str(datetime.datetime.now().isoformat()))

        guild = self.bot.get_guild(GUILD_ID)
        users = guild.members

        mentor_role = discord.utils.get(guild.roles, id=MENTOR_ROLE)

        training_staff_role = discord.utils.get(guild.roles, id=TRAINING_STAFF_ROLE)

        mentors = await Roles.get_mentors(self)

        moderators = await Roles.get_moderators(self)

        for user in users:            
            try:
                cid = re.findall('\d+', str(user.nick))

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
              

            except ValueError as e:
                if mentor_role in user.roles:
                    await user.remove_roles(mentor_role, reason=self.NO_CID_REMOVE_REASON)
                    
            except Exception as e:
                print(e)
                continue

        print("check_roles finished at " + str(datetime.datetime.now().isoformat()))

    @tasks.loop(seconds=CHECK_MENTORS_INTERVAL)
    async def check_roles_loop(self):
        await self.check_roles()

    @cog_ext.cog_slash(name="checkroles", guild_ids=GUILD_ID, description="Check mentor & training staff roles")
    @commands.has_any_role(*staff_roles())
    async def check_mentors_command(self, ctx):
        await ctx.send("Staff refresh in progress")
        await self.check_roles(True)
        await ctx.send("Staff refresh process finished")

def setup(bot):
    bot.add_cog(RolesCog(bot))

