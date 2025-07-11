import re
import time
from typing import Any

import discord
from discord.ext import commands

from helpers.faq import faq_triggers, send_faq_embed


class FAQ(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

        # Load FAQ responses from markdown files
        self.faqs: dict[str, str] = {
            'ATC Application': self._load_faq('faq_atc.md'),
            'Visiting/Transfer': self._load_faq('faq_visiting.md'),
            'Waiting Time': self._load_faq('faq_waiting.md'),
        }

        # Define triggers and threshold for each FAQ
        self.faq_triggers: dict[str, dict[str, Any]] = faq_triggers

        # Store (channel_id, topic): last_reply_time
        self.recent_replies: dict[tuple[int, str], float] = {}

    def _load_faq(self, filename: str) -> str:
        try:
            with open(f'messages/{filename}', encoding='utf8') as f:
                return f.read()
        except Exception as e:
            return f'Error reading {filename}: {e}'

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
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

        words: set[str] = set(re.findall(r'\b\w+\b', content))
        now: float = time.time()
        one_hour: int = 3600

        # Unified FAQ check loop
        for topic, data in self.faq_triggers.items():
            matches = data['triggers'] & words
            if len(matches) >= data['threshold']:
                key = (message.channel.id, topic)
                last_time = self.recent_replies.get(key, 0)

                if now - last_time < one_hour:
                    return

                self.recent_replies[key] = now
                await send_faq_embed(
                    message.channel, message.author.mention, topic, self.faqs[topic]
                )
                return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FAQ(bot))
