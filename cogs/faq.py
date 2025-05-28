import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
import re
import time

class FAQ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Load the ATC FAQ response from the markdown file.
        try:
            with open('messages/faq_atc.md', "r", encoding="utf8") as f:
                self.atc_response = f.read()
        except Exception as e:
            self.atc_response = f"Error reading faq_atc.md: {e}"

        # Load the Visiting FAQ response from the markdown file.
        try:
            with open('messages/faq_visiting.md', "r", encoding="utf8") as f:
                self.visiting_response = f.read()
        except Exception as e:
            self.visiting_response = f"Error reading faq_visiting.md: {e}"

        # Load the Waiting time FAQ response from the markdown file.
        try:
            with open('messages/faq_waiting.md', "r", encoding="utf8") as f:
                self.waiting_response = f.read()
        except Exception as e:
            self.waiting_response = f"Error reading faq_waiting.md: {e}"

        # Store (user_id, faq_type, question_hash): last_reply_time
        self.recent_replies = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        # Prevent the bot from responding to itself or other bots.
        if message.author.bot:
            return

        # Skip messages over 400 characters
        if len(message.content) > 400:
            return

        content = message.content.lower()
        user_id = message.author.id

        # Define trigger keywords for each FAQ.
        # ATC trigger words, one line per language
        atc_triggers = {
            # EN
            "application", "apply", "atc", "become", "controller", "train", "training",
            # DK
            "ansøgning", "ansøge", "blive", "flygeleder", "træning",
            # NO
            "søknad", "søke", "søker", "bli", "flygeleder", "trening",
            # SE
            "ansökan", "ansöka", "ansöker", "bli", "flygledare", "utbildning", "träning",
            # FI
            "hakemus", "hakea", "haen", "lennonjohtaja", "harjoittelu", "koulutus", "tulla",
            # IS
            "umsókn", "sækja", "sækist", "flugumferðarstjóri", "þjálfun", "verða", "menntun"
        }
        atc_tolerance = 2

        # Visiting/Transfer trigger words, one line per language
        visiting_triggers = {
            # EN
            "transfer", "visiting",
            # DK
            "besøg", "besøge", "besøger", "flytte", "flytter", "overførsel", "overføring",
            # NO
            "overføring", "overføre", "overfører", "besøke", "besøker", "flytte", "flytter",
            # SE
            "besöka", "besöker", "flytta", "flyttar", "överföring", "överföra", "överför",
            # FI
            "vierailla", "vierailee", "siirtyä", "siirto", "siirtää",
            # IS
            "heimsækja", "heimsækir", "flytja", "flytur", "skipta", "skiptir", "flutningur"
        }
        visiting_tolerance = 1

        # Waiting time trigger words, one line per language
        waiting_triggers = {
            # EN
            "wait", "waiting", "estimate", "approx", "time", "queue", "training",
            # DK
            "ventetid", "vente", "venter", "kø", "tid", "træning",
            # NO
            "ventetid", "vente", "venter", "kø", "tid", "trening",
            # SE
            "väntetid", "vänta", "väntar", "kö", "tid", "träning",
            # FI
            "odottaa", "odotusaika", "aika", "jono", "harjoittelu",
            # IS
            "bíða", "bíður", "biðtími", "biðröð", "tími", "þjálfun"
        }
        waiting_tolerance = 2

        # Tokenize message using regex to extract words
        words = set(re.findall(r'\b\w+\b', content))

        # Only respond if there's a question mark in the message
        if "?" not in content:
            return

        # Helper to hash the question for deduplication
        def question_hash(trigger_type):
            # Use a tuple of trigger type and sorted words as a simple hash
            return (trigger_type, tuple(sorted(words)))

        now = time.time()
        one_hour = 1

        # Helper function to send a nicely formatted embed
        async def send_faq_embed(channel, user_mention, topic, description):
            await channel.send(f"{user_mention} I believe you're asking about the {topic.lower()}:")
            embed = discord.Embed(
                description=description,
                color=discord.Color(0x43c6e7)
            )
            await channel.send(embed=embed)

        # Check for ATC related keywords.
        atc_matches = atc_triggers & words
        if len(atc_matches) >= atc_tolerance:
            key = (user_id, "atc", question_hash("atc"))
            last_time = self.recent_replies.get(key, 0)
            if now - last_time < one_hour:
                return
            self.recent_replies[key] = now
            await send_faq_embed(
                message.channel,
                message.author.mention,
                "ATC Application",
                self.atc_response
            )
            return

        # Check for Visiting related keywords.
        visiting_matches = visiting_triggers & words
        if len(visiting_matches) >= visiting_tolerance:
            key = (user_id, "visiting", question_hash("visiting"))
            last_time = self.recent_replies.get(key, 0)
            if now - last_time < one_hour:
                return
            self.recent_replies[key] = now
            await send_faq_embed(
                message.channel,
                message.author.mention,
                "Visiting/Transfer",
                self.visiting_response
            )
            return

        # Check for Waiting time related keywords
        waiting_matches = waiting_triggers & words
        if len(waiting_matches) >= waiting_tolerance:
            key = (user_id, "waiting", question_hash("waiting"))
            last_time = self.recent_replies.get(key, 0)
            if now - last_time < one_hour:
                return
            self.recent_replies[key] = now
            await send_faq_embed(
                message.channel,
                message.author.mention,
                "Waiting Time",
                self.waiting_response
            )
            return


async def setup(bot):
    await bot.add_cog(FAQ(bot))
