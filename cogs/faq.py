import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
import re
import time
from helpers.faq import send_faq_embed


class FAQ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Load FAQ responses from markdown files
        self.faqs = {
            'ATC Application': self._load_faq('faq_atc.md'),
            'Visiting/Transfer': self._load_faq('faq_visiting.md'),
            'Waiting Time': self._load_faq('faq_waiting.md'),
        }

        # Define triggers and tolerances for each FAQ
        self.faq_triggers = {
            'ATC Application': {
                'triggers': {
                    # EN
                    'application',
                    'apply',
                    'atc',
                    'become',
                    'controller',
                    'train',
                    'training',
                    # DK
                    'ansøgning',
                    'ansøge',
                    'blive',
                    'flygeleder',
                    'træning',
                    # NO
                    'søknad',
                    'søke',
                    'søker',
                    'bli',
                    'flygeleder',
                    'trening',
                    # SE
                    'ansökan',
                    'ansöka',
                    'ansöker',
                    'bli',
                    'flygledare',
                    'utbildning',
                    'träning',
                    # FI
                    'hakemus',
                    'hakea',
                    'haen',
                    'lennonjohtaja',
                    'harjoittelu',
                    'koulutus',
                    'tulla',
                    # IS
                    'umsókn',
                    'sækja',
                    'sækist',
                    'flugumferðarstjóri',
                    'þjálfun',
                    'verða',
                    'menntun',
                },
                'tolerance': 2,
            },
            'Visiting/Transfer': {
                'triggers': {
                    # EN
                    'transfer',
                    'visiting',
                    # DK
                    'besøg',
                    'besøge',
                    'besøger',
                    'flytte',
                    'flytter',
                    'overførsel',
                    'overføring',
                    # NO
                    'overføring',
                    'overføre',
                    'overfører',
                    'besøke',
                    'besøker',
                    'flytte',
                    'flytter',
                    # SE
                    'besöka',
                    'besöker',
                    'flytta',
                    'flyttar',
                    'överföring',
                    'överföra',
                    'överför',
                    # FI
                    'vierailla',
                    'vierailee',
                    'siirtyä',
                    'siirto',
                    'siirtää',
                    # FI
                    'heimsækja',
                    'heimsækir',
                    'flytja',
                    'flytur',
                    'skipta',
                    'skiptir',
                    'flutningur',
                },
                'tolerance': 1,
            },
            'Waiting Time': {
                'triggers': {
                    # EN
                    'wait',
                    'waiting',
                    'estimate',
                    'approx',
                    'time',
                    'queue',
                    'training',
                    # DK
                    'ventetid',
                    'vente',
                    'venter',
                    'kø',
                    'tid',
                    'træning',
                    # NO
                    'ventetid',
                    'vente',
                    'venter',
                    'kø',
                    'tid',
                    'trening',
                    # SE
                    'väntetid',
                    'vänta',
                    'väntar',
                    'kö',
                    'tid',
                    'träning',
                    # FI
                    'odottaa',
                    'odotusaika',
                    'aika',
                    'jono',
                    'harjoittelu',
                    # IS
                    'bíða',
                    'bíður',
                    'biðtími',
                    'biðröð',
                    'tími',
                    'þjálfun',
                },
                'tolerance': 2,
            },
        }

        # Store (user_id, faq_type, question_hash): last_reply_time
        self.recent_replies = {}

    def _load_faq(self, filename):
        try:
            with open(f'messages/{filename}', 'r', encoding='utf8') as f:
                return f.read()
        except Exception as e:
            return f'Error reading {filename}: {e}'

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from bots
        if message.author.bot:
            return

        # Ignore very long messages, high chance it's not relevant
        if len(message.content) > 400:
            return

        content = message.content.lower()

        # Only respond if there's a question mark in the message
        if '?' not in content:
            return

        words = set(re.findall(r'\b\w+\b', content))
        now = time.time()
        one_hour = 3600

        # Unified FAQ check loop
        for topic, data in self.faq_triggers.items():
            matches = data['triggers'] & words
            if len(matches) >= data['tolerance']:
                key = (message.channel.id, topic)
                last_time = self.recent_replies.get(key, 0)

                if now - last_time < one_hour:
                    return

                self.recent_replies[key] = now
                await send_faq_embed(
                    message.channel, message.author.mention, topic, self.faqs[topic]
                )
                return


async def setup(bot):
    await bot.add_cog(FAQ(bot))
