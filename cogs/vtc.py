import os

import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import mysql.connector
from helpers.config import S1, S2, S3, C1, VTC_CHANNEL, VTC_STAFFING_MSG

today = datetime.date.today()
next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
date_formatted = next_monday.strftime("%d/%m/%Y")

mydb = mysql.connector.connect(
    host="localhost",
    user=os.getenv('BOT_DB_USER'),
    password=os.getenv('BOT_DB_PASSWORD'),
    database=os.getenv('BOT_DB_NAME')
    )

class VTCcog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autoreset.start()

    def cog_unload(self):
        self.autoreset.cancel()

    @commands.command(name="setupvtc", hidden=True, brief='Bot sends VTC staffing message')
    async def setupvtc(self, ctx) -> None:
        username = ctx.message.author.id
        if ctx.channel.id == VTC_CHANNEL:
        
            if ctx.message.author.id == 263767489895333889 or 332493772934086656 or 414877211238334474 or 207885223159922688:
                await ctx.message.delete()
                await ctx.send("Vectors to Copenhagen staffing thread for the next event on Monday " + str(date_formatted) + " Main positions should be staffed first.\n\nSign up for your position by writing #requested position (E.G. #EKCH_TWR). The position is automatically booked\nShould you need to cancel write '#Cancel' and your booking will be removed. Please DO NOT do this at the last minute. If you cancel a main position please make arrangement to make sure it is covered by someone else!\n\nMain Positions: \nEKDK_CTR: \nEKCH_APP: \nEKCH_TWR: \nEKCH_GND:\n\nSecondary Positions:\nEKCH_DEL: \nEKDK_V_CTR: \nEKDK_D_CTR: \nEKCH_F_APP: \nEKCH_DEP: \nEKCH_C_TWR: \nEKCH_D_TWR: \n\nRegional Positions:\nEKBI_APP: \nEKBI_TWR: \nEKYT_APP: \nEKYT_TWR: \nEKKA_TWR: \nEKKA_APP: \nEKAH_APP: \nEKAH_TWR: ")
            else:
                await ctx.send("<@" + str(username) + "> You are not allowed to use this command!")
        else: 
            await ctx.send("<@" + str(username) + "> Please use the <#" + str(VTC_CHANNEL) + "> channel")


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

    @commands.command(name="EKCH_DEL", hidden=True, brief='Function to signup for EKCH_DEL.')
    async def ekch_del(self, ctx) -> None:
        

        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            if S1_rating in ctx.author.roles:

                S1cursor = mydb.cursor()
            
                S1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S1_sql = S1cursor.fetchone()

                if S1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='1'"

                    S1cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_DEL!")   
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)            
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='1'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_DEL!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                   
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='1'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_DEL!") 
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                   
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='1'"

                    C1cursor.execute(sql)
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
            await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @commands.command(name="EKCH_GND", hidden=True, brief='Function to signup for EKCH_GND.')
    async def ekch_gnd(self, ctx) -> None:
        

        S1_rating = discord.utils.get(ctx.guild.roles, id=S1)
        S2_rating = discord.utils.get(ctx.guild.roles, id=S2)
        S3_rating = discord.utils.get(ctx.guild.roles, id=S3)
        C1_rating = discord.utils.get(ctx.guild.roles, id=C1)

        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            if S1_rating in ctx.author.roles:

                S1cursor = mydb.cursor()
            
                S1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S1_sql = S1cursor.fetchone()

                if S1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='2'"

                    S1cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_GND!")    
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='2'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_GND!")      
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='2'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_GND!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                else:
                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='2'"

                    C1cursor.execute(sql)
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
            if S1_rating in ctx.author.roles:

                S1cursor = mydb.cursor()
            
                S1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S1_sql = S1cursor.fetchone()

                if S1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='3'"

                    S1cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='3'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_TWR!")   
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='3'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                  
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='3'"

                    C1cursor.execute(sql)
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
            if S1_rating in ctx.author.roles:

                S1cursor = mydb.cursor()
            
                S1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S1_sql = S1cursor.fetchone()

                if S1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='4'"

                    S1cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_C_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='4'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_C_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='4'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_C_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='4'"

                    C1cursor.execute(sql)
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
            if S1_rating in ctx.author.roles:

                S1cursor = mydb.cursor()
            
                S1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S1_sql = S1cursor.fetchone()

                if S1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='5'"

                    S1cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_D_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                else:
                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='5'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_D_TWR!") 
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                   
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='5'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_D_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                else:
                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='5'"

                    C1cursor.execute(sql)
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
            if S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='6'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_DEP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='6'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_DEP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                   
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='6'"

                    C1cursor.execute(sql)
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
            if S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='7'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                  
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='7'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='7'"

                    C1cursor.execute(sql)
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
            if S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='8'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_F_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                  
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='8'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKCH_F_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='8'"

                    C1cursor.execute(sql)
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
            if S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='9'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKBI_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='9'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKBI_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)           
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='9'"

                    C1cursor.execute(sql)
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
            if S1_rating in ctx.author.roles:

                S1cursor = mydb.cursor()
            
                S1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S1_sql = S1cursor.fetchone()

                if S1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='10'"

                    S1cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKBI_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)             
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='10'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKBI_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)            
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='10'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKBI_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)             
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='10'"

                    C1cursor.execute(sql)
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
            if S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='11'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKYT_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='11'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKYT_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)             
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='11'"

                    C1cursor.execute(sql)
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
            if S1_rating in ctx.author.roles:

                S1cursor = mydb.cursor()
            
                S1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S1_sql = S1cursor.fetchone()

                if S1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='12'"

                    S1cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKYT_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)               
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='12'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKYT_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)          
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='12'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKYT_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)               
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='12'"

                    C1cursor.execute(sql)
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
            if S1_rating in ctx.author.roles:

                S1cursor = mydb.cursor()
            
                S1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S1_sql = S1cursor.fetchone()

                if S1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='13'"

                    S1cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKKA_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)              
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='13'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKKA_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)             
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='13'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKKA_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)               
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='13'"

                    C1cursor.execute(sql)
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
            if S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='14'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKKA_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)           
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='14'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKKA_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)               
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='14'"

                    C1cursor.execute(sql)
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
            if S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='15'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKAH_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='15'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKAH_APP!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                 
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='15'"

                    C1cursor.execute(sql)
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
            if S1_rating in ctx.author.roles:

                S1cursor = mydb.cursor()
            
                S1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S1_sql = S1cursor.fetchone()

                if S1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='16'"

                    S1cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKAH_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                  
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S2_rating in ctx.author.roles:
                S2cursor = mydb.cursor()
            
                S2cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S2_sql = S2cursor.fetchone()

                if S2_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='16'"

                    S2cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKAH_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='16'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKAH_TWR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)               
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='16'"

                    C1cursor.execute(sql)
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
            if S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='17'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKDK_CTR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='17'"

                    C1cursor.execute(sql)
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
            if S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='18'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKDK_V_CTR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)             
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='18'"

                    C1cursor.execute(sql)
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
            if S3_rating in ctx.author.roles:
                S3cursor = mydb.cursor()
            
                S3cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                S3_sql = S3cursor.fetchone()

                if S3_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='19'"

                    S3cursor.execute(sql)
                    mydb.commit()
                    await self.updatepositions(ctx)
                    await ctx.send("<@" + str(usernick) + "> Confirmed booking for EKDK_D_CTR!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)                
                else:

                    await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)

            elif C1_rating in ctx.author.roles:
                C1cursor = mydb.cursor()
            
                C1cursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
                C1_sql = C1cursor.fetchone()

                if C1_sql == None:
                    sql = "UPDATE vtc SET name = '" + str(usernick) + "' WHERE id ='19'"

                    C1cursor.execute(sql)
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

        #EKDK d CTR
        EKDKdCursor = mydb.cursor()
        EKDKdCursor.execute("SELECT name FROM vtc WHERE id = '19'")
        ekdk_d_ctr_sql = EKDKdCursor.fetchone()

        message = await ctx.fetch_message(VTC_STAFFING_MSG)
        await message.edit(content="Vectors to Copenhagen staffing thread for the next event on Monday " + str(date_formatted) + ". Main positions should be staffed first.\n\nSign up for your position by writing #requested position (E.G. #EKCH_TWR). The position is automatically booked\nShould you need to cancel write '#Cancel' and your booking will be removed. Please DO NOT do this at the last minute. If you cancel a main position please make arrangement to make sure it is covered by someone else!\n\nMain Positions: \nEKDK_CTR: <@" + str(ekdk_ctr_sql[0]) + "> \nEKCH_APP: <@" + str(ekch_app_sql[0]) + "> \nEKCH_TWR: <@" + str(ekch_twr_sql[0]) + "> \nEKCH_GND: <@" + str(ekch_gnd_sql[0]) + "> \n\nSecondary Positions:\nEKCH_DEL: <@" + str(ekch_del_sql[0]) + "> \nEKDK_V_CTR: <@" + str(ekdk_v_ctr_sql[0]) + "> \nEKDK_D_CTR: <@" + str(ekdk_d_ctr_sql[0]) + "> \nEKCH_F_APP: <@" + str(ekch_f_app_sql[0]) + "> \nEKCH_DEP: <@" + str(ekch_dep_sql[0]) + "> \nEKCH_C_TWR: <@" + str(ekch_c_twr_sql[0]) + "> \nEKCH_D_TWR: <@" + str(ekch_d_twr_sql[0]) + "> \n\nRegional Positions:\nEKBI_APP: <@" + str(ekbi_app_sql[0]) + "> \nEKBI_TWR: <@" + str(ekbi_twr_sql[0]) + "> \nEKYT_APP: <@" + str(ekyt_app_sql[0]) + "> \nEKYT_TWR: <@" + str(ekyt_twr_sql[0]) + "> \nEKKA_TWR: <@" + str(ekka_twr_sql[0]) + "> \nEKKA_APP: <@" + str(ekka_app_sql[0]) + "> \nEKAH_APP: <@" + str(ekah_app_sql[0]) + "> \nEKAH_TWR: <@" + str(ekah_twr_sql[0]) + "> ")
        

    @commands.command(name="Cancel", hidden=True, brief='Function to cancel your requested position.')
    async def cancel(self, ctx) -> None:
        usernick = ctx.message.author.id

        if ctx.channel.id == VTC_CHANNEL:
            Cancelcursor = mydb.cursor()
            
            Cancelcursor.execute("SELECT name FROM vtc WHERE name = '" + str(usernick) + "'")
            cancel_sql = Cancelcursor.fetchone()
            
            if cancel_sql == None:
                await ctx.send("<@" + str(usernick) + "> You don't have a booking!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
            else:
                sql = "UPDATE vtc SET name = '' WHERE name = '" + str(usernick) + "'"

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

    




