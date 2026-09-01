from collections.abc import Callable

import discord
import discord.abc
import structlog

logger = structlog.stdlib.get_logger()

HELPFUL, UNHELPFUL = '\N{THUMBS UP SIGN}', '\N{THUMBS DOWN SIGN}'
FEEDBACK_EMOJI = (HELPFUL, UNHELPFUL)
FEEDBACK_NOTE = f'{HELPFUL} or {UNHELPFUL} to tell us whether this helped'


async def send_faq_embed(
    channel: discord.abc.Messageable,
    user_mention: str,
    topic: str,
    description: str,
    remember: Callable[[discord.Message], None],
    reference: discord.Message | None = None,
    intro: str | None = None,
) -> discord.Message:
    """
    Post an FAQ answer in a channel.

    ``remember`` is handed the posted answer before the reactions go on. A vote
    can arrive the moment our own first reaction does, and whoever counts votes
    has to know what the answer was about by then.

    Pass ``reference`` to post it as a reply to the message that asked, and
    ``intro`` to replace the hedged lead-in the automatic answers use. A person
    who picked the topic themselves is not guessing.
    """
    embed = discord.Embed(description=description, color=discord.Color(0x43C6E7))
    embed.set_footer(text=FEEDBACK_NOTE)
    content = intro or f"{user_mention} I believe you're asking about {topic}:"

    if reference is not None:
        message = await channel.send(
            content, embed=embed, reference=reference, mention_author=False
        )
    else:
        message = await channel.send(content, embed=embed)

    remember(message)

    await add_feedback_reactions(message)

    return message


async def add_feedback_reactions(message: discord.Message) -> None:
    """
    Offer the two reactions people vote with.

    Nobody has to hunt for the right emoji, and a missing permission costs us
    the vote rather than the answer. One emoji failing does not hold back the
    other, so a hiccup on the way up still leaves a way down.
    """
    for emoji in FEEDBACK_EMOJI:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            logger.warning('Could not add an FAQ feedback reaction', emoji=emoji)
