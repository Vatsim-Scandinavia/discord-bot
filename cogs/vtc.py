import os

import discord
from discord.ext import commands, tasks
from discord_slash import cog_ext, SlashContext
import datetime
import asyncio
import mysql.connector
from helpers.config import S1, S2, S3, C1, VTC_CHANNEL, VTC_STAFFING_MSG, GUILD_ID
from helpers.message import roles

today = datetime.date.today()
next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
date_formatted = next_monday.strftime("%d/%m/%Y")

mydb = mysql.connector.connect(
    host="localhost",
    user=os.getenv('BOT_DB_USER'),
    password=os.getenv('BOT_DB_PASSWORD'),
    database=os.getenv('BOT_DB_NAME')
    )

guild_ids = [GUILD_ID]

guild = GUILD_ID



class VTCcog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autoreset.start()

    def cog_unload(self):
        self.autoreset.cancel()

    @cog_ext.cog_slash(name="setupvtc", guild_ids=guild_ids, description="Bot sends VTC staffing message")
    @commands.has_any_role(*roles())
    async def setupvtc(self, ctx: SlashContext):
        username = ctx.author.id
        if ctx.channel.id == VTC_CHANNEL:
        
            if ctx.author.id == 263767489895333889 or 332493772934086656 or 414877211238334474 or 207885223159922688:
                msg = await ctx.send("Vectors to Copenhagen staffing message is being generated")
                await msg.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                await ctx.send("Vectors to Copenhagen staffing thread for the next event on Monday " + str(date_formatted) + " Main positions should be staffed first.\n\nSign up for your position by writing #requested position (E.G. #EKCH_TWR). The position is automatically booked\nShould you need to cancel write '#Cancel' and your booking will be removed. Please DO NOT do this at the last minute. If you cancel a main position please make arrangement to make sure it is covered by someone else!\n\nMain Positions: \nEKDK_CTR: \nEKCH_APP: \nEKCH_TWR: \nEKCH_GND:\n\nSecondary Positions:\nEKCH_DEL: \nEKDK_V_CTR: \nEKDK_D_CTR: \nEKCH_F_APP: \nEKCH_DEP: \nEKCH_C_TWR: \nEKCH_D_TWR: \n\nRegional Positions:\nEKBI_APP: \nEKBI_TWR: \nEKYT_APP: \nEKYT_TWR: \nEKKA_TWR: \nEKKA_APP: \nEKAH_APP: \nEKAH_TWR: ")
            else:
                await ctx.send("<@" + str(username) + "> You are not allowed to use this command!")
        else: 
            await ctx.send("<@" + str(username) + "> Please use the <#" + str(VTC_CHANNEL) + "> channel")
        

    """@commands.command(name="setupvtc", hidden=True, brief='Bot sends VTC staffing message')
    async def setupvtc(self, ctx):
        username = ctx.message.author.id
        if ctx.channel.id == VTC_CHANNEL:
        
            if ctx.message.author.id == 263767489895333889 or 332493772934086656 or 414877211238334474 or 207885223159922688:
                await ctx.message.delete()
                await ctx.send("Vectors to Copenhagen staffing thread for the next event on Monday " + str(date_formatted) + " Main positions should be staffed first.\n\nSign up for your position by writing #requested position (E.G. #EKCH_TWR). The position is automatically booked\nShould you need to cancel write '#Cancel' and your booking will be removed. Please DO NOT do this at the last minute. If you cancel a main position please make arrangement to make sure it is covered by someone else!\n\nMain Positions: \nEKDK_CTR: \nEKCH_APP: \nEKCH_TWR: \nEKCH_GND:\n\nSecondary Positions:\nEKCH_DEL: \nEKDK_V_CTR: \nEKDK_D_CTR: \nEKCH_F_APP: \nEKCH_DEP: \nEKCH_C_TWR: \nEKCH_D_TWR: \n\nRegional Positions:\nEKBI_APP: \nEKBI_TWR: \nEKYT_APP: \nEKYT_TWR: \nEKKA_TWR: \nEKKA_APP: \nEKAH_APP: \nEKAH_TWR: ")
            else:
                await ctx.send("<@" + str(username) + "> You are not allowed to use this command!")
        else: 
            await ctx.send("<@" + str(username) + "> Please use the <#" + str(VTC_CHANNEL) + "> channel")"""


    @commands.command(name="manreset", hidden=True, brief='Bot manually resets the chat.')
    async def manreset(self, ctx) -> None:
        username = ctx.message.author.id
        if ctx.channel.id == VTC_CHANNEL:

            if ctx.message.author.id == 263767489895333889 or 332493772934086656 or 414877211238334474 or 207885223159922688:
                mancursor = mydb.cursor()
                sql = "UPDATE vtc SET name = '' WHERE id < 19"
                mancursor.execute(sql)
                mydb.commit()
                await self.updatepositions(ctx)
                await ctx.send("The chat is being manually reset!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=None, check=lambda msg: not msg.pinned)
            else:
                await ctx.send("<@" + str(username) + "> You are not allowed to use this command!")
        else:
            await ctx.send("<@" + str(username) + "> Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @cog_ext.cog_slash(name="EKCH_DEL", guild_ids=guild_ids, description="Function to signup for EKCH_DEL.")
    async def ekch_del(self, ctx) -> None:
        usernick = ctx.author.id

        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='1'")
            booked_sql = bookedcursor.fetchone()
            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
            else:
                if S1_rating in ctx.author.roles or S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    Delcursor = mydb.cursor()
                    Delcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    Del_sql = Delcursor.fetchone()
                    if Del_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='1'"
                        Delcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_DEL!")    
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKCH_GND", hidden=True, brief='Function to signup for EKCH_GND.')
    async def ekch_gnd(self, ctx) -> None:
        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:

            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='2'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S1_rating in ctx.author.roles or S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:

                    Delcursor = mydb.cursor()
            
                    Delcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    Del_sql = Delcursor.fetchone()

                    if Del_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='2'"

                        Delcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_GND!")    
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKCH_TWR", hidden=True, brief='Function to signup for EKCH_TWR.')
    async def ekch_twr(self, ctx) -> None:
        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='3'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S1_rating in ctx.author.roles or S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    Twrcursor = mydb.cursor()
            
                    Twrcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    Twr_sql = Twrcursor.fetchone()

                    if Twr_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='3'"

                        Twrcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_TWR!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKCH_C_TWR", hidden=True, brief='Function to signup for EKCH_C_TWR.')
    async def ekch_c_twr(self, ctx) -> None:
        
        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='4'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S1_rating in ctx.author.roles or S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:

                    CTwrcursor = mydb.cursor()
            
                    CTwrcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    CTwr_sql = CTwrcursor.fetchone()

                    if CTwr_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='4'"

                        CTwrcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_C_TWR!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKCH_D_TWR", hidden=True, brief='Function to signup for EKCH_D_TWR.')
    async def ekch_d_twr(self, ctx) -> None:
        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='5'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S1_rating in ctx.author.roles or S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:

                    DTwrcursor = mydb.cursor()
            
                    DTwrcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    DTwr_sql = DTwrcursor.fetchone()

                    if DTwr_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='5'"

                        DTwrcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_D_TWR!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKCH_DEP", hidden=True, brief='Function to signup for EKCH_DEP.')
    async def ekch_dep(self, ctx) -> None:
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='6'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    Depcursor = mydb.cursor()
            
                    Depcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    Dep_sql = Depcursor.fetchone()

                    if Dep_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='6'"

                        Depcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_DEP!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKCH_APP", hidden=True, brief='Function to signup for EKCH_APP.')
    async def ekch_app(self, ctx) -> None:
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='7'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    Appcursor = mydb.cursor()
        
                    Appcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    App_sql = Appcursor.fetchone()

                    if App_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='7'"

                        Appcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_APP!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                  
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKCH_F_APP", hidden=True, brief='Function to signup for EKCH_F_APP.')
    async def ekch_f_app(self, ctx) -> None:
        
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:

            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='8'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:

                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    FAppcursor = mydb.cursor()
                    FAppcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    FApp_sql = FAppcursor.fetchone()

                    if FApp_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='8'"

                        FAppcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_F_APP!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                  
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKBI_APP", hidden=True, brief='Function to signup for EKBI_APP.')
    async def ekbi_app(self, ctx) -> None:
        
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='9'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    BIAppcursor = mydb.cursor()
            
                    BIAppcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    BIApp_sql = BIAppcursor.fetchone()

                    if BIApp_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='9'"

                        BIAppcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKBI_APP!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKBI_TWR", hidden=True, brief='Function to signup for EKBI_TWR.')
    async def ekbi_twr(self, ctx) -> None:
        
        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:

            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='10'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S1_rating in ctx.author.roles or S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:

                    BIAppcursor = mydb.cursor()
            
                    BIAppcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    BIApp_sql = BIAppcursor.fetchone()

                    if BIApp_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='10'"

                        BIAppcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKBI_TWR!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)             
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKYT_APP", hidden=True, brief='Function to signup for EKYT_APP.')
    async def ekyt_app(self, ctx) -> None:
        
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:

            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='11'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    AALAppcursor = mydb.cursor()
            
                    AALAppcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    AALApp_sql = AALAppcursor.fetchone()

                    if AALApp_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='11'"

                        AALAppcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKYT_APP!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKYT_TWR", hidden=True, brief='Function to signup for EKYT_TWR.')
    async def ekyt_twr(self, ctx) -> None:
        
        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='12'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S1_rating in ctx.author.roles or S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    AALTwrcursor = mydb.cursor()
                    AALTwrcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    AALTwr_sql = AALTwrcursor.fetchone()

                    if AALTwr_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='12'"

                        AALTwrcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKYT_TWR!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)               
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKKA_TWR", hidden=True, brief='Function to signup for EKKA_TWR.')
    async def ekka_twr(self, ctx) -> None:
        
        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='13'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:

                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:

                if S1_rating in ctx.author.roles or S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    KRPTwrcursor = mydb.cursor()
            
                    KRPTwrcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    KRPTwr_sql = KRPTwrcursor.fetchone()

                    if KRPTwr_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='13'"

                        KRPTwrcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKKA_TWR!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)              
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKKA_APP", hidden=True, brief='Function to signup for EKKA_APP.')
    async def ekka_app(self, ctx) -> None:
        
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='14'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    KRPAppcursor = mydb.cursor()
            
                    KRPAppcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    KRPApp_sql = KRPAppcursor.fetchone()

                    if KRPApp_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='14'"

                        KRPAppcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKKA_APP!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)           
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKAH_APP", hidden=True, brief='Function to signup for EKAH_APP.')
    async def ekah_app(self, ctx) -> None:
        
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='15'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:

                if S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    AARAppcursor = mydb.cursor()
            
                    AARAppcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    AARApp_sql = AARAppcursor.fetchone()

                    if AARApp_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='15'"

                        AARAppcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKAH_APP!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKAH_TWR", hidden=True, brief='Function to signup for EKAH_TWR.')
    async def ekah_twr(self, ctx) -> None:
        
        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='16'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S1_rating in ctx.author.roles or S2_rating in ctx.author.roles or S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:

                    AARTwrcursor = mydb.cursor()
            
                    AARTwrcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    AARTwr_sql = AARTwrcursor.fetchone()

                    if AARTwr_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='16'"

                        AARTwrcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKAH_TWR!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                  
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKDK_CTR", hidden=True, brief='Function to signup for EKDK_CTR.')
    async def ekdk_ctr(self, ctx) -> None:
        
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='17'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:

                if S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    EKDKCtrcursor = mydb.cursor()
                    EKDKCtrcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    EKDKCtr_sql = EKDKCtrcursor.fetchone()

                    if EKDKCtr_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='17'"

                        EKDKCtrcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKDK_CTR!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKDK_V_CTR", hidden=True, brief='Function to signup for EKDK_V_CTR.')
    async def ekdk_v_ctr(self, ctx) -> None:
        
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='18'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    EKDKvCtrcursor = mydb.cursor()
                    EKDKvCtrcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    EKDKvCtr_sql = EKDKvCtrcursor.fetchone()

                    if EKDKvCtr_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='18'"

                        EKDKvCtrcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKDK_V_CTR!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)             
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKDK_D_CTR", hidden=True, brief='Function to signup for EKDK_D_CTR.')
    async def ekdk_d_ctr(self, ctx) -> None:
        
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            bookedcursor = mydb.cursor()
            
            bookedcursor.execute("SELECT name FROM vtc WHERE name='' and id='19'")
            booked_sql = bookedcursor.fetchone()

            if booked_sql == None:
                await ctx.send("<@" + str(usernick) + "> This position has already been booked!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                
            else:
                if S3_rating in ctx.author.roles or C1_rating in ctx.author.roles:
                    EKDKdCtrcursor = mydb.cursor()
            
                    EKDKdCtrcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                    EKDKdCtr_sql = EKDKdCtrcursor.fetchone()

                    if EKDKdCtr_sql == None:
                        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE id ='19'"

                        EKDKdCtrcursor.execute(sql)
                        mydb.commit()
                        await self.updatepositions(ctx)
                        await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKDK_D_CTR!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                    else:
                        await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You are not allowed to book this position!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else: 
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    async def updatepositions(self, ctx) -> None:      
        #Delivery
        delCursor = mydb.cursor()
        delCursor.execute("SELECT name FROM vtc WHERE id = '1'")
        ekch_del_sql = delCursor.fetchone()

        #Apron
        gndCursor = mydb.cursor()
        gndCursor.execute("SELECT name FROM vtc WHERE id = '2'")
        ekch_gnd_sql = gndCursor.fetchone()

        #Tower
        twrCursor = mydb.cursor()
        twrCursor.execute("SELECT name FROM vtc WHERE id = '3'")
        ekch_twr_sql = twrCursor.fetchone()

        #Crossing Tower
        CtwrCursor = mydb.cursor()
        CtwrCursor.execute("SELECT name FROM vtc WHERE id = '4'")
        ekch_c_twr_sql = CtwrCursor.fetchone()

        #Departure Tower
        DtwrCursor = mydb.cursor()
        DtwrCursor.execute("SELECT name FROM vtc WHERE id = '5'")
        ekch_d_twr_sql = DtwrCursor.fetchone()

        #Departure
        depCursor = mydb.cursor()
        depCursor.execute("SELECT name FROM vtc WHERE id = '6'")
        ekch_dep_sql = depCursor.fetchone()

        #Approach
        appCursor = mydb.cursor()
        appCursor.execute("SELECT name FROM vtc WHERE id = '7'")
        ekch_app_sql = appCursor.fetchone()

        #Final Approach
        fappCursor = mydb.cursor()
        fappCursor.execute("SELECT name FROM vtc WHERE id = '8'")
        ekch_f_app_sql = fappCursor.fetchone()

        #BLL Approach
        bappCursor = mydb.cursor()
        bappCursor.execute("SELECT name FROM vtc WHERE id = '9'")
        ekbi_app_sql = bappCursor.fetchone()

        #BLL Tower
        btwrCursor = mydb.cursor()
        btwrCursor.execute("SELECT name FROM vtc WHERE id = '10'")
        ekbi_twr_sql = btwrCursor.fetchone()

        #AAL Approach
        AALappCursor = mydb.cursor()
        AALappCursor.execute("SELECT name FROM vtc WHERE id = '11'")
        ekyt_app_sql = AALappCursor.fetchone()

        #AAL Tower
        AALtwrCursor = mydb.cursor()
        AALtwrCursor.execute("SELECT name FROM vtc WHERE id = '12'")
        ekyt_twr_sql = AALtwrCursor.fetchone()

        #KRP Tower
        KRPtwrCursor = mydb.cursor()
        KRPtwrCursor.execute("SELECT name FROM vtc WHERE id = '13'")
        ekka_twr_sql = KRPtwrCursor.fetchone()

        #KRP Approach
        KRPappCursor = mydb.cursor()
        KRPappCursor.execute("SELECT name FROM vtc WHERE id = '14'")
        ekka_app_sql = KRPappCursor.fetchone()

        #AAR Approach
        AARappCursor = mydb.cursor()
        AARappCursor.execute("SELECT name FROM vtc WHERE id = '15'")
        ekah_app_sql = AARappCursor.fetchone()

        #AAR Tower
        AARtwrCursor = mydb.cursor()
        AARtwrCursor.execute("SELECT name FROM vtc WHERE id = '16'")
        ekah_twr_sql = AARtwrCursor.fetchone()

        #EKDK CTR
        EKDKCursor = mydb.cursor()
        EKDKCursor.execute("SELECT name FROM vtc WHERE id = '17'")
        ekdk_ctr_sql = EKDKCursor.fetchone()

        #EKDK V CTR
        EKDKvCursor = mydb.cursor()
        EKDKvCursor.execute("SELECT name FROM vtc WHERE id = '18'")
        ekdk_v_ctr_sql = EKDKvCursor.fetchone()

        #EKDK D CTR
        EKDKdCursor = mydb.cursor()
        EKDKdCursor.execute("SELECT name FROM vtc WHERE id = '19'")
        ekdk_d_ctr_sql = EKDKdCursor.fetchone()

        message = await ctx.fetch_message(VTC_STAFFING_MSG)
        await message.edit(content="Vectors to Copenhagen staffing thread for the next event on Monday " + str(date_formatted) + ". Main positions should be staffed first.\n\nSign up for your position by writing #requested position (E.G. #EKCH_TWR). The position is automatically booked\nShould you need to cancel write '#Cancel' and your booking will be removed. Please DO NOT do this at the last minute. If you cancel a main position please make arrangement to make sure it is covered by someone else!\n\nMain Positions: \nEKDK_CTR:" + str(ekdk_ctr_sql[0]) + " \nEKCH_APP: " + str(ekch_app_sql[0]) + " \nEKCH_TWR: " + str(ekch_twr_sql[0]) + " \nEKCH_GND: " + str(ekch_gnd_sql[0]) + " \n\nSecondary Positions:\nEKCH_DEL: " + str(ekch_del_sql[0]) + " \nEKDK_V_CTR: " + str(ekdk_v_ctr_sql[0]) + " \nEKDK_D_CTR: " + str(ekdk_d_ctr_sql[0]) + " \nEKCH_F_APP: " + str(ekch_f_app_sql[0]) + " \nEKCH_DEP: " + str(ekch_dep_sql[0]) + " \nEKCH_C_TWR: " + str(ekch_c_twr_sql[0]) + " \nEKCH_D_TWR: " + str(ekch_d_twr_sql[0]) + " \n\nRegional Positions:\nEKBI_APP: " + str(ekbi_app_sql[0]) + " \nEKBI_TWR: " + str(ekbi_twr_sql[0]) + " \nEKYT_APP: " + str(ekyt_app_sql[0]) + " \nEKYT_TWR: " + str(ekyt_twr_sql[0]) + " \nEKKA_TWR: " + str(ekka_twr_sql[0]) + " \nEKKA_APP: " + str(ekka_app_sql[0]) + " \nEKAH_APP: " + str(ekah_app_sql[0]) + " \nEKAH_TWR: " + str(ekah_twr_sql[0]) + " ")
        

    @commands.command(name="Cancel", hidden=True, brief='Function to cancel your requested position.')
    async def cancel(self, ctx) -> None:
        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            Cancelcursor = mydb.cursor()
            
            Cancelcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
            cancel_sql = Cancelcursor.fetchone()
            
            if cancel_sql == None:
                await ctx.send("<@" + str(usernick) + "> You don't have a booking!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
            else:
                sql = "UPDATE vtc SET name = '' WHERE name = '<@" + str(usernick) + ">'"

                Cancelcursor.execute(sql)
                mydb.commit()
                await self.updatepositions(ctx)
                await ctx.send("<@" + str(usernick) + "> Confirmed cancelling of your booking!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
            
        else:
            await ctx.send("<@" + str(usernick) + "> Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @tasks.loop(seconds=60)
    async def autoreset(self) -> None:

        now = datetime.datetime.now()
        if now.weekday() == 0 and now.hour == 23 and 00 <= now.minute <= 5:
            mancursor = mydb.cursor()
            sql = "UPDATE vtc SET name = '' WHERE id < 19"
            mancursor.execute(sql)
            mydb.commit()
            await self.bot.wait_until_ready()
            channel = self.bot.get_channel(int(VTC_CHANNEL))
            msg = await channel.fetch_message(VTC_STAFFING_MSG)
            await msg.edit(content="Vectors to Copenhagen staffing thread for the next event on Monday " + str(date_formatted) + " Main positions should be staffed first.\n\nSign up for your position by writing #requested position (E.G. #EKCH_TWR). The position is automatically booked\nShould you need to cancel write '#Cancel' and your booking will be removed. Please DO NOT do this at the last minute. If you cancel a main position please make arrangement to make sure it is covered by someone else!\n\nMain Positions: \nEKDK_CTR: \nEKCH_APP: \nEKCH_TWR: \nEKCH_GND:\n\nSecondary Positions:\nEKCH_DEL: \nEKDK_V_CTR: \nEKDK_D_CTR: \nEKCH_F_APP: \nEKCH_DEP: \nEKCH_C_TWR: \nEKCH_D_TWR: \n\nRegional Positions:\nEKBI_APP: \nEKBI_TWR: \nEKYT_APP: \nEKYT_TWR: \nEKKA_TWR: \nEKKA_APP: \nEKAH_APP: \nEKAH_TWR: ")
            await channel.send("The chat is being automatic reset!")
            await asyncio.sleep(1)
            await channel.purge(limit=None, check=lambda msg: not msg.pinned)

def setup(bot):
    bot.add_cog(VTCcog(bot))