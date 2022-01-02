import discord
import re

from discord.ext import commands, tasks
from discord_slash import cog_ext
import datetime
from helpers.config import CHECK_MENTORS_INTERVAL, DEBUG, GUILD_ID, MENTOR_ROLE, ROLE_REASONS
from helpers.mentor import Mentor
from helpers.message import staff_roles

class MentorsCog(commands.Cog):

    MENTOR_ROLE_ADD_REASON = ROLE_REASONS['mentor_add']
    MENTOR_ROLE_REMOVE_REASON = ROLE_REASONS['mentor_remove']
    NO_CID_REMOVE_REASON = ROLE_REASONS['no_cid']
    NO_AUTH_REMOVE_REASON = ROLE_REASONS['no_auth']

    GUILD_ID = [GUILD_ID]
    
    def __init__(self, bot):
        self.bot = bot
        self.check_mentors_loop.start()
    
    def cog_unload(self):
        self.check_mentors_loop.cancel()

    
    async def check_mentors(self, override=False):
        await self.bot.wait_until_ready()
        if DEBUG == True and override == False:
            print("check_mentors skipped due to DEBUG ON. You can start manually with command instead.")
            return
            
        print("check_mentors started at " + str(datetime.datetime.now().isoformat()))

        guild = self.bot.get_guild(GUILD_ID)
        users = guild.members

        mentor_role = discord.utils.get(guild.roles, id=MENTOR_ROLE)

        mentors = await Mentor.get_mentors(self)

        for user in users:            
            try:
                cid = re.findall('\d+', str(user.nick))

                if len(cid) < 1:
                    raise ValueError

                should_be_mentor = False

                for mentor in mentors:
                    if int(mentor['id']) == int(cid[0]):
                        should_be_mentor = True
                        
                if mentor_role not in user.roles and should_be_mentor == True:
                    await user.add_roles(mentor_role, reason=self.MENTOR_ROLE_ADD_REASON)
                elif mentor_role in user.roles and should_be_mentor == False:
                    await user.remove_roles(mentor_role, reason=self.MENTOR_ROLE_REMOVE_REASON)
              

            except ValueError as e:
                if mentor_role in user.roles:
                    await user.remove_roles(mentor_role, reason=self.NO_CID_REMOVE_REASON)
                    
            except Exception as e:
                print(e)
                continue

        print("check_mentors finished at " + str(datetime.datetime.now().isoformat()))

    @tasks.loop(seconds=CHECK_MENTORS_INTERVAL)
    async def check_mentors_loop(self):
        await self.check_mentors()

    @cog_ext.cog_slash(name="checkmentors", guild_ids=GUILD_ID, description="Check mentors")
    @commands.has_any_role(*staff_roles())
    async def check_mentors_command(self, ctx):
        await ctx.send("Mentor refresh in progress")
        await self.check_mentors(True)
        await ctx.send("Mentor refresh process finished")

def setup(bot):
    bot.add_cog(MentorsCog(bot))

