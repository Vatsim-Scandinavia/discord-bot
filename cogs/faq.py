import time
from collections import OrderedDict
from collections.abc import Callable

import discord
import structlog
from discord import app_commands, ui
from discord.ext import commands

from core.faq import FaqMatcher, load_topics
from helpers.config import config
from helpers.faq import HELPFUL, UNHELPFUL, send_faq_embed

logger = structlog.stdlib.get_logger()

ANSWER_MENU_NAME = 'Answer with FAQ'

# How many answers we keep track of for feedback. Votes on anything older, or
# on anything posted before a restart, are ignored.
FEEDBACK_MEMORY = 500


class FAQ(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

        # One Markdown file per topic, answer and triggers together. Reload
        # them after an edit with /reload faq, no restart needed.
        self.topics = load_topics()
        self.matcher = FaqMatcher(self.topics)

        # Store (channel_id, topic): last_reply_time
        self.recent_replies: dict[tuple[int, str], float] = {}

        # Store answer message_id: topic, so a vote knows what it is about
        self.answered: OrderedDict[int, str] = OrderedDict()

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
        ranked = self.matcher.rank(message.content)
        topics = ranked + [topic for topic in self.topics if topic not in ranked]

        await interaction.response.send_message(
            f'Which FAQ should I reply to {message.author.display_name} with?',
            view=FAQTopicView(self, message, topics),
            ephemeral=True,
        )

    def resting_since(self, channel_id: int, title: str, now: float) -> float | None:
        """
        Return when this topic last answered in this channel, or None.

        Only while it is still on cooldown. One rule, asked by both the
        automatic answers and the people picking a topic by hand.
        """
        last_time = self.recent_replies.get((channel_id, title))

        if last_time is None or now - last_time >= self.topics[title].cooldown:
            return None

        return last_time

    def claim(self, channel_id: int, title: str, now: float) -> float | None:
        """
        Hold this topic in this channel while its answer is on its way.

        Returns what stood there before, to hand back if the answer never
        lands. A claim is a reservation, not an answer that went out.
        """
        previous = self.recent_replies.get((channel_id, title))
        self.recent_replies[(channel_id, title)] = now

        return previous

    def release(self, channel_id: int, title: str, previous: float | None) -> None:
        """Undo a claim, so an answer that never landed costs nothing."""
        if previous is None:
            self.recent_replies.pop((channel_id, title), None)
            return

        self.recent_replies[(channel_id, title)] = previous

    def remember_answer(self, message_id: int, topic: str) -> None:
        """Note what an answer was about, forgetting the oldest to stay bounded."""
        self.answered[message_id] = topic

        while len(self.answered) > FEEDBACK_MEMORY:
            self.answered.popitem(last=False)

    def remembering(self, topic: str) -> Callable[[discord.Message], None]:
        """Hand out the note-taker for one topic, for an answer about to be posted."""
        return lambda posted: self.remember_answer(posted.id, topic)

    def record_feedback(self, payload: discord.RawReactionActionEvent) -> bool:
        """
        Log a vote on one of our answers.

        Only logged, never acted on. It is there to be counted later, so we can
        see which topics are landing and which triggers need retuning.
        """
        topic = self.answered.get(payload.message_id)
        emoji = str(payload.emoji)

        if topic is None or emoji not in (HELPFUL, UNHELPFUL):
            return False

        if self.bot.user and payload.user_id == self.bot.user.id:
            return False

        logger.info(
            'FAQ feedback',
            topic=topic,
            helpful=emoji == HELPFUL,
            user_id=payload.user_id,
            channel_id=payload.channel_id,
        )

        return True

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        self.record_feedback(payload)

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

        # The cooldown holds back one topic in one channel, not the whole
        # message. A topic that has not answered here recently still may, even
        # when a better matching topic is resting.
        for title in self.matcher.rank(content):
            if self.resting_since(message.channel.id, title, now) is not None:
                continue

            previous = self.claim(message.channel.id, title, now)

            try:
                await send_faq_embed(
                    message.channel,
                    message.author.mention,
                    title,
                    self.topics[title].answer,
                    remember=self.remembering(title),
                )
            except discord.HTTPException:
                # Nothing was said, so nothing is resting. A kept claim would
                # silence this topic here for the whole cooldown and have the
                # picker report an answer that was never posted.
                logger.exception(
                    'Could not post the FAQ answer',
                    topic=title,
                    channel_id=message.channel.id,
                )
                self.release(message.channel.id, title, previous)
                return

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

        topic = self.values[0]
        now = time.time()
        answered_at = self.cog.resting_since(self.target.channel.id, topic, now)

        # This topic has just been answered here, by the bot or by someone
        # else with the same menu. Say so instead of repeating it. No view is
        # passed, which leaves the picker in place, so another topic can still
        # be chosen; passing None would take it away.
        if answered_at is not None:
            await interaction.response.edit_message(
                content=(
                    f'**{topic}** was already answered in this channel '
                    f'<t:{int(answered_at)}:R>. Pick another topic if that '
                    f'answer did not cover it.'
                )
            )
            return

        self.claimed = True

        # Claim the cooldown before posting rather than after, so a question
        # arriving while this reply is in flight does not get the same answer
        # from the bot on its own.
        previous = self.cog.claim(self.target.channel.id, topic, now)

        try:
            await send_faq_embed(
                self.target.channel,
                self.target.author.mention,
                topic,
                self.cog.topics[topic].answer,
                remember=self.cog.remembering(topic),
                reference=self.target,
                intro=f'{self.target.author.mention} this should answer it:',
            )
        except discord.HTTPException:
            logger.exception(
                'Could not post the FAQ reply',
                topic=topic,
                channel_id=self.target.channel.id,
            )
            self._release(topic, previous)
            await interaction.response.send_message(
                'I could not post that reply. Check that I am allowed to post '
                'in that channel and that the message is still there.',
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            content=f'Replied with **{topic}**.', view=None
        )

    def _release(self, topic: str, previous: float | None) -> None:
        """Hand the claim back and take another pick, the reply having failed."""
        self.claimed = False
        self.cog.release(self.target.channel.id, topic, previous)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FAQ(bot))
