import os
import discord
from discord.ext import commands, tasks
from discord_slash import cog_ext
import datetime
import asyncio
import mysql.connector
from helpers.config import VTC_CHANNEL, VTC_STAFFING_MSG, GUILD_ID, VTC_POSITIONS
from helpers.message import staff_roles

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

class VTCcog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autoreset.start()

    def cog_unload(self):
        self.autoreset.cancel()

    @cog_ext.cog_slash(name="setupvtc", guild_ids=guild_ids, description="Bot sends VTC staffing message")
    @commands.has_any_role(*staff_roles())
    async def setupvtc(self, ctx):
        username = ctx.author.id
        if ctx.channel.id == VTC_CHANNEL:
            msg = await ctx.send("Message is being generated")
            await msg.channel.purge(limit=2, check=lambda msg: not msg.pinned)
            await ctx.send("Vectors for Copenhagen staffing – Monday " + str(date_formatted) + "\n\nSchedules: https://vatsim-scandinavia.org/forums/topic/3745-vectors-to-copenhagen-schedules-2021/ \n\nWe want to encourage you to follow these guidelines to optimize the process.\n- Force Majeure is happening to all of us, but generally sign up, only when you firmly believe you are able to attend\n- If you had a position last week, consider giving other people a chance, before booking the same position again\n- Please do not forget to unbook if you are unable to participate, and advise a staff member or the Facebook group.\n\nInstructions:\n- To book a postion enter “/book [name of position]” (e.g. /book EKCH_APP)\n- If you need to cancel a position enter “/unbook [name of position] (e.g. /unbook EKCH_APP)\n- Booking in VATBOOK must be done SEPERATELY: https://cc.vatsim-scandinavia.org/vatbook \n- Main positions must be booked first\n\nMain Positions: \nEKDK_CTR: \nEKCH_APP: \nEKCH_TWR: \nEKCH_GND:\n\nSecondary Positions:\nEKCH_DEL: \nEKDK_V_CTR: \nEKDK_D_CTR: \nEKCH_F_APP: \nEKCH_DEP: \nEKCH_C_TWR: \nEKCH_D_TWR: \n\nRegional Positions:\nEKBI_APP: \nEKBI_TWR: \nEKYT_APP: \nEKYT_TWR: \nEKKA_TWR: \nEKKA_APP: \nEKAH_APP: \nEKAH_TWR: ")
        else: 
            await ctx.send("<@" + str(username) + "> Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @cog_ext.cog_slash(name="manreset", guild_ids=guild_ids, description="Bot manually resets the chat and the staffing.")
    @commands.has_any_role(*staff_roles())
    async def manreset(self, ctx, mydb):
        username = ctx.author.id
        if ctx.channel.id == VTC_CHANNEL:
            mydb.reconnect()
            mancursor = mydb.cursor()
            sql = "UPDATE vtc SET name = '' WHERE id < 19"
            mancursor.execute(sql)
            mydb.commit()
            await self.updatepositions(ctx)
            await ctx.send("The chat is being manually reset!")
            await asyncio.sleep(5)
            await ctx.channel.purge(limit=None, check=lambda msg: not msg.pinned)
        else:
            await ctx.send("<@" + str(username) + "> Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @cog_ext.cog_slash(name="book", guild_ids=guild_ids, description="Function to book position")
    async def book(self, ctx, position: str):
        usernick = ctx.author.id
        try:
            if ctx.channel.id == VTC_CHANNEL:
                mydb.reconnect()
                bookedcursor = mydb.cursor()
                bookedcursor.execute("SELECT name FROM vtc WHERE name='' and position='" + position + "'")
                booked_sql = bookedcursor.fetchone()
                if booked_sql == None:
                    await ctx.send("<@" + str(usernick) + "> an error has occurred!")
                    await asyncio.sleep(5)
                    await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
                else:
                    if position in VTC_POSITIONS:
                        mydb.reconnect()
                        cursor = mydb.cursor()
                        cursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
                        sql = cursor.fetchone()
                        if sql == None:
                            await self.bookposition(ctx, position, cursor)
                        else:
                            await ctx.send("<@" + str(usernick) + "> You already have a booking!")
                            await asyncio.sleep(5)
                            await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
            else:
                await ctx.send("Please use the <#" + str(VTC_CHANNEL) + "> channel")

        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')

    async def bookposition(self, ctx, position: str, cursor) -> None:
        usernick = ctx.author.id
        sql = "UPDATE vtc SET name = '<@" + str(usernick) + ">' WHERE position ='" + position + "'"
        cursor.execute(sql)
        mydb.commit()
        await self.updatepositions(ctx)
        await ctx.send("<@" + str(usernick) + "> Confirmed booking for " + position + "!")    
        await asyncio.sleep(5)
        await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        
    async def updatepositions(self, ctx) -> None:      
        mydb.reconnect()

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

        #Departure Tower
        DtwrCursor = mydb.cursor()
        DtwrCursor.execute("SELECT name FROM vtc WHERE id = '4'")
        ekch_d_twr_sql = DtwrCursor.fetchone()

        #Crossing Tower
        CtwrCursor = mydb.cursor()
        CtwrCursor.execute("SELECT name FROM vtc WHERE id = '5'")
        ekch_c_twr_sql = CtwrCursor.fetchone()

        #Approach
        appCursor = mydb.cursor()
        appCursor.execute("SELECT name FROM vtc WHERE id = '6'")
        ekch_app_sql = appCursor.fetchone()


        #Final Approach
        fappCursor = mydb.cursor()
        fappCursor.execute("SELECT name FROM vtc WHERE id = '7'")
        ekch_f_app_sql = fappCursor.fetchone()

        #Departure
        depCursor = mydb.cursor()
        depCursor.execute("SELECT name FROM vtc WHERE id = '8'")
        ekch_dep_sql = depCursor.fetchone()

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

        #KRP Approach
        KRPappCursor = mydb.cursor()
        KRPappCursor.execute("SELECT name FROM vtc WHERE id = '13'")
        ekka_app_sql = KRPappCursor.fetchone()

        #KRP Tower
        KRPtwrCursor = mydb.cursor()
        KRPtwrCursor.execute("SELECT name FROM vtc WHERE id = '14'")
        ekka_twr_sql = KRPtwrCursor.fetchone()

        #AAR Tower
        AARtwrCursor = mydb.cursor()
        AARtwrCursor.execute("SELECT name FROM vtc WHERE id = '15'")
        ekah_twr_sql = AARtwrCursor.fetchone()

        #AAR Approach
        AARappCursor = mydb.cursor()
        AARappCursor.execute("SELECT name FROM vtc WHERE id = '16'")
        ekah_app_sql = AARappCursor.fetchone()

        #EKDK CTR
        EKDKCursor = mydb.cursor()
        EKDKCursor.execute("SELECT name FROM vtc WHERE id = '17'")
        ekdk_ctr_sql = EKDKCursor.fetchone()

        #EKDK D CTR
        EKDKdCursor = mydb.cursor()
        EKDKdCursor.execute("SELECT name FROM vtc WHERE id = '18'")
        ekdk_d_ctr_sql = EKDKdCursor.fetchone()

        #EKDK V CTR
        EKDKvCursor = mydb.cursor()
        EKDKvCursor.execute("SELECT name FROM vtc WHERE id = '19'")
        ekdk_v_ctr_sql = EKDKvCursor.fetchone()

        channel = self.bot.get_channel(int(VTC_CHANNEL))
        message = await channel.fetch_message(VTC_STAFFING_MSG)
        await message.edit(content="Vectors for Copenhagen staffing – Monday " + str(date_formatted) + "\n\nSchedules: https://vatsim-scandinavia.org/forums/topic/3745-vectors-to-copenhagen-schedules-2021/ \n\nWe want to encourage you to follow these guidelines to optimize the process.\n- Force Majeure is happening to all of us, but generally sign up, only when you firmly believe you are able to attend\n- If you had a position last week, consider giving other people a chance, before booking the same position again\n- Please do not forget to unbook if you are unable to participate, and advise a staff member or the Facebook group.\n\nInstructions:\n- To book a postion enter “/book [name of position]” (e.g. /book EKCH_APP)\n- If you need to cancel a position enter “/unbook [name of position] (e.g. /unbook EKCH_APP)\n- Booking in VATBOOK must be done SEPERATELY: https://cc.vatsim-scandinavia.org/vatbook \n- Main positions must be booked first\n\nMain Positions: \nEKDK_CTR: " + str(ekdk_ctr_sql[0]) + "\nEKCH_APP: " + str(ekch_app_sql[0]) + "\nEKCH_TWR: " + str(ekch_twr_sql[0]) + "\nEKCH_GND: " + str(ekch_gnd_sql[0]) + "\n\nSecondary Positions:\nEKCH_DEL: " + str(ekch_del_sql[0]) + "\nEKDK_V_CTR: " + str(ekdk_v_ctr_sql[0]) + "\nEKDK_D_CTR: " + str(ekdk_d_ctr_sql[0]) + "\nEKCH_F_APP: " + str(ekch_f_app_sql[0]) + "\nEKCH_DEP: " + str(ekch_dep_sql[0]) + "\nEKCH_C_TWR: " + str(ekch_c_twr_sql[0]) + "\nEKCH_D_TWR: " + str(ekch_d_twr_sql[0]) + "\n\nRegional Positions:\nEKBI_APP: " + str(ekbi_app_sql[0]) + "\nEKBI_TWR: " + str(ekbi_twr_sql[0]) + "\nEKYT_APP: " + str(ekyt_app_sql[0]) + "\nEKYT_TWR: " + str(ekyt_twr_sql[0]) + "\nEKKA_TWR: " + str(ekka_twr_sql[0]) + "\nEKKA_APP: " + str(ekka_app_sql[0]) + "\nEKAH_APP: " + str(ekah_app_sql[0]) + "\nEKAH_TWR: " + str(ekah_twr_sql[0]) + " ")
        
    @cog_ext.cog_slash(name="Unbook", guild_ids=guild_ids, description="Function to cancel your requested position.")
    async def cancel(self, ctx) -> None:
        usernick = ctx.author.id
        if ctx.channel.id == VTC_CHANNEL:
            mydb.reconnect()
            Cancelcursor = mydb.cursor()
            Cancelcursor.execute("SELECT name FROM vtc WHERE name = '<@" + str(usernick) + ">'")
            cancel_sql = Cancelcursor.fetchone()
            if cancel_sql == None:
                await ctx.send("<@" + str(usernick) + "> You don't have a booking!")
                await asyncio.sleep(5)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
            else:
                sql = "UPDATE vtc SET name = '' WHERE name = '<@" + str(usernick) + ">'"
                Cancelcursor.execute(sql)
                mydb.commit()
                await self.updatepositions(ctx)
                await ctx.send("<@" + str(usernick) + "> Confirmed cancelling of your booking!")
                await asyncio.sleep(5)
                await ctx.channel.purge(limit=2, check=lambda msg: not msg.pinned)
        else:
            await ctx.send("<@" + str(usernick) + "> Please use the <#" + str(VTC_CHANNEL) + "> channel")

    @tasks.loop(seconds=60)
    async def autoreset(self) -> None:
        await self.bot.wait_until_ready()
        now = datetime.datetime.now()
        if now.weekday() == 0 and now.hour == 23 and 00 <= now.minute <= 1:
            mydb.reconnect()
            mancursor = mydb.cursor()
            sql = "UPDATE vtc SET name = '' WHERE id < 19"
            mancursor.execute(sql)
            mydb.commit()
            await self.bot.wait_until_ready()
            channel = self.bot.get_channel(int(VTC_CHANNEL))
            msg = await channel.fetch_message(VTC_STAFFING_MSG)
            await msg.edit(content="Vectors for Copenhagen staffing – Monday " + str(date_formatted) + "\n\nSchedules: https://vatsim-scandinavia.org/forums/topic/3745-vectors-to-copenhagen-schedules-2021/ \n\nWe want to encourage you to follow these guidelines to optimize the process.\n- Force Majeure is happening to all of us, but generally sign up, only when you firmly believe you are able to attend\n- If you had a position last week, consider giving other people a chance, before booking the same position again\n- Please do not forget to unbook if you are unable to participate, and advise a staff member or the Facebook group.\n\nInstructions:\n- To book a postion enter “/book [name of position]” (e.g. /book EKCH_APP)\n- If you need to cancel a position enter “/unbook [name of position] (e.g. /unbook EKCH_APP)\n- Booking in VATBOOK must be done SEPERATELY: https://cc.vatsim-scandinavia.org/vatbook \n- Main positions must be booked first\n\nMain Positions: \nEKDK_CTR: \nEKCH_APP: \nEKCH_TWR: \nEKCH_GND:\n\nSecondary Positions:\nEKCH_DEL: \nEKDK_V_CTR: \nEKDK_D_CTR: \nEKCH_F_APP: \nEKCH_DEP: \nEKCH_C_TWR: \nEKCH_D_TWR: \n\nRegional Positions:\nEKBI_APP: \nEKBI_TWR: \nEKYT_APP: \nEKYT_TWR: \nEKKA_TWR: \nEKKA_APP: \nEKAH_APP: \nEKAH_TWR: ")
            await channel.send("The chat is being automatic reset!")
            await asyncio.sleep(5)
            await channel.purge(limit=None, check=lambda msg: not msg.pinned)

def setup(bot):
    bot.add_cog(VTCcog(bot))