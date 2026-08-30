import re
import time
from collections import Counter
from typing import Any

import discord
import structlog
from discord import app_commands, ui
from discord.ext import commands

from helpers.config import config
from helpers.faq import faq_triggers, send_faq_embed

logger = structlog.stdlib.get_logger()

ANSWER_MENU_NAME = 'Answer with FAQ'


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

        # How much each trigger word says about which topic is meant
        self.trigger_weights: dict[str, float] = self._build_trigger_weights(
            self.faq_triggers
        )

        # Store (channel_id, topic): last_reply_time
        self.recent_replies: dict[tuple[int, str], float] = {}

        # Context menus cannot be declared with a decorator inside a cog, so
        # build it here and hand the tree the bound method.
        self.answer_menu = app_commands.ContextMenu(
            name=ANSWER_MENU_NAME, callback=self.answer_with_faq
        )
        self.bot.tree.add_command(self.answer_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.answer_menu.name, type=self.answer_menu.type)

    @app_commands.checks.has_any_role(
        *config.STAFF_ROLES,
        config.MENTOR_ROLE,
        config.BUDDY_ROLE,
        config.TRAINING_STAFF_ROLE,
    )
    @app_commands.guild_only()
    async def answer_with_faq(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        """Answer someone else's message with an FAQ, chosen from a menu."""
        ranked = self.rank_topics(message.content)
        topics = ranked + [topic for topic in self.faqs if topic not in ranked]

        await interaction.response.send_message(
            f'Which FAQ should I reply to {message.author.display_name} with?',
            view=FAQTopicView(self, message, topics),
            ephemeral=True,
        )

    def _load_faq(self, filename: str) -> str:
        try:
            with open(f'messages/{filename}', encoding='utf8') as f:
                return f.read()
        except Exception as e:
            return f'Error reading {filename}: {e}'

    @staticmethod
    def _build_trigger_weights(
        triggers: dict[str, dict[str, Any]],
    ) -> dict[str, float]:
        """
        Weigh every trigger by how many topics claim it.

        A word only one topic uses identifies that topic. A word several topics
        share says little about which of them is meant, so it counts for less.
        """
        topic_count: Counter[str] = Counter()
        for data in triggers.values():
            topic_count.update(data['triggers'])

        return {word: 1 / count for word, count in topic_count.items()}

    def rank_topics(self, content: str) -> list[str]:
        """
        Return the topics whose triggers the message clears, best match first.

        Thresholds still gate on the plain number of matched triggers, so which
        topics qualify is unchanged. The weights only decide the order among
        them, which is what stops a shared word like "training" from handing the
        answer to whichever topic happens to be defined first.
        """
        words: set[str] = set(re.findall(r'\b\w+\b', content.lower()))

        scored: list[tuple[float, str]] = []
        for topic, data in self.faq_triggers.items():
            matches = data['triggers'] & words
            if len(matches) >= data['threshold']:
                score = sum(self.trigger_weights[word] for word in matches)
                scored.append((score, topic))

        # Stable, so topics that score the same stay in definition order.
        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [topic for _, topic in scored]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Ignore messages from bots
        if message.author.bot:
            return

        # Ignore very long messages, high chance it's not relevant
        if len(message.content) > 400:
            return

        # Ignore messages from TRAINING_STAFF_ROLE and MENTOR_ROLE
        if any(
            role.id in [config.TRAINING_STAFF_ROLE, config.MENTOR_ROLE]
            for role in message.author.roles
        ):
            return

        content = message.content.lower()

        # Only respond if there's a question mark, or the words "how" or "where" in the message
        trigger_words = [
            'how',
            'where',
            # Danish
            'hvordan',
            'hvor',
            # Finnish
            'miten',
            'missä',
            # Swedish
            'hur',
            'var',
            # Norwegian
            'hvordan',
            'hvor',
            # Icelandic
            'hvernig',
            'hvar',
        ]
        if '?' not in content and not any(word in content for word in trigger_words):
            return

        now: float = time.time()
        one_hour: int = 3600

        # The cooldown holds back one topic in one channel, not the whole
        # message. A topic that has not answered here recently still may, even
        # when a better matching topic is resting.
        for topic in self.rank_topics(content):
            key = (message.channel.id, topic)
            last_time = self.recent_replies.get(key, 0)

            if now - last_time < one_hour:
                continue

            self.recent_replies[key] = now
            await send_faq_embed(
                message.channel, message.author.mention, topic, self.faqs[topic]
            )
            return


class FAQTopicView(ui.View):
    """Ephemeral topic picker shown after the context menu is used."""

    def __init__(self, cog: 'FAQ', target: discord.Message, topics: list[str]) -> None:
        super().__init__(timeout=120)
        self.add_item(FAQTopicSelect(cog, target, topics))


class FAQTopicSelect(ui.Select):
    def __init__(self, cog: 'FAQ', target: discord.Message, topics: list[str]) -> None:
        self.cog = cog
        self.target = target
        self.claimed = False
        """Set as soon as a pick is taken, so a second one cannot answer twice."""

        # The best guess sits at the top, so the common case is one click.
        super().__init__(
            placeholder='Pick the FAQ that answers this',
            options=[discord.SelectOption(label=topic) for topic in topics],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        # The picker stays live while the reply is posting. Without this, a
        # second pick in that window posts the answer a second time.
        if self.claimed:
            await interaction.response.defer()
            return

        self.claimed = True
        topic = self.values[0]
        key = (self.target.channel.id, topic)
        previous = self.cog.recent_replies.get(key)

        # Claim the cooldown before posting rather than after, so a question
        # arriving while this reply is in flight does not get the same answer
        # from the bot on its own.
        self.cog.recent_replies[key] = time.time()

        try:
            await send_faq_embed(
                self.target.channel,
                self.target.author.mention,
                topic,
                self.cog.faqs[topic],
                reference=self.target,
                intro=f'{self.target.author.mention} this should answer it:',
            )
        except discord.HTTPException:
            logger.exception(
                'Could not post the FAQ reply',
                topic=topic,
                channel_id=self.target.channel.id,
            )
            self._release(key, previous)
            await interaction.response.send_message(
                'I could not post that reply. Check that I am allowed to post '
                'in that channel and that the message is still there.',
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            content=f'Replied with **{topic}**.', view=None
        )

    def _release(self, key: tuple[int, str], previous: float | None) -> None:
        """Undo the cooldown claim, so a reply that never landed costs nothing."""
        self.claimed = False

        if previous is None:
            self.cog.recent_replies.pop(key, None)
            return

        self.cog.recent_replies[key] = previous


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FAQ(bot))
