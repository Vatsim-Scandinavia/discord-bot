from discord.ext import commands, tasks
import discord
from helpers.config import VATSIM_MEMBER_ROLE, CHECK_MEMBERS_INTERVAL

class TasksCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.checkMembers.start()

    def cog_unload(self):
        self.checkMembers.cancel()

    @tasks.loop(seconds=CHECK_MEMBERS_INTERVAL)
    async def checkMembers(self):
        guild = self.bot.get_guild(776110954437148672)
        users = guild.members
        for user in users:
            if discord.utils.get(guild.roles, name=VATSIM_MEMBER_ROLE) not in user.roles:
                continue

            cid = [int(s) for s in user.nick.split() if s.isdigit()]

def setup(bot):
    bot.add_cog(TasksCog(bot))