import discord
import discord.abc


async def send_faq_embed(
    channel: discord.abc.Messageable,
    user_mention: str,
    topic: str,
    description: str,
    reference: discord.Message | None = None,
    intro: str | None = None,
) -> None:
    """
    Post an FAQ answer in a channel.

    Pass ``reference`` to post it as a reply to the message that asked, and
    ``intro`` to replace the hedged lead-in the automatic answers use. A person
    who picked the topic themselves is not guessing.
    """
    embed = discord.Embed(description=description, color=discord.Color(0x43C6E7))
    content = intro or f"{user_mention} I believe you're asking about {topic}:"

    if reference is not None:
        await channel.send(
            content, embed=embed, reference=reference, mention_author=False
        )
        return

    await channel.send(content, embed=embed)
