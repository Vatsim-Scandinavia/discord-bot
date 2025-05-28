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

        content = message.content.lower()
        user_id = message.author.id

        # Define trigger keywords for each FAQ.
        atc_triggers = {
            # EN:
            "application", "apply", "atc", "become", "controller", "train", "training",
            # DK
            "ansøgning", "ansøge", "blive", "flygeleder", "træning", "uddannelse",
            # NO
            "søknad", "søke", "bli", "flygeleder", "trening", "utdanning",
            # SE
            "ansökan", "ansöka", "bli", "flygledare", "utbildning",
            # FI
            "hakemus", "hakea", "lennonjohtaja", "harjoittelu", "koulutus", "tulla",
            # IS
            "umsókn", "sækja", "flugumferðarstjóri", "þjálfun", "verða", "menntun"
        }

        # Visiting/Transfer trigger words, one line per language
        visiting_triggers = {
            # EN
            "move", "migrate", "switch", "transfer", "visiting",
            # DK
            "besøg", "besøge", "flytte", "overførsel", "overføring",
            # NO
            "besøke", "flytte", "overføring",
            # SE
            "besöka", "flytta", "överföring",
            # FI
            "vierailla", "siirtyä", "siirto",
            # IS
            "heimsækja", "flytja", "skipta"
        }

        # Waiting time trigger words, one line per language
        waiting_triggers = {
            # EN
            "wait", "waiting", "estimate", "approx", "time", "queue",
            # DK
            "ventetid", "vente", "kø", "tid",
            # NO
            "ventetid", "vente", "kø", "tid",
            # SE
            "väntetid", "vänta", "kö", "tid",
            # FI
            "odottaa", "odotusaika", "aika", "jono",
            # IS
            "bíða", "biðtími", "biðröð"
        }

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

        # Check for ATC related keywords.
        if atc_triggers & words:
            key = (user_id, "atc", question_hash("atc"))
            last_time = self.recent_replies.get(key, 0)
            if now - last_time < one_hour:
                return
            self.recent_replies[key] = now
            await message.channel.send(f"{message.author.mention} {self.atc_response}")
            return

        # Check for Visiting related keywords.
        if visiting_triggers & words:
            key = (user_id, "visiting", question_hash("visiting"))
            last_time = self.recent_replies.get(key, 0)
            if now - last_time < one_hour:
                return
            self.recent_replies[key] = now
            await message.channel.send(f"{message.author.mention} {self.visiting_response}")
            return

        # Check for Waiting time related keywords
        if waiting_triggers & words:
            key = (user_id, "waiting", question_hash("waiting"))
            last_time = self.recent_replies.get(key, 0)
            if now - last_time < one_hour:
                return
            self.recent_replies[key] = now
            await message.channel.send(f"{message.author.mention} {self.waiting_response}")
            return


async def setup(bot):
    await bot.add_cog(FAQ(bot))
