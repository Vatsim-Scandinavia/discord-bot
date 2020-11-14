from discord.ext import commands, tasks

class TasksCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(seconds=5)
    async def checkMembers(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                print(member.username)

def setup(bot):
    bot.add_cog(TasksCog(bot))