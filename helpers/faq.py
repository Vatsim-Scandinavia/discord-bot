from helpers.config import config
import discord

async def send_faq_embed(channel, user_mention, topic, description):
    await channel.send(f"{user_mention} I believe you're asking about the {topic.lower()}:")
    embed = discord.Embed(
        description=description,
        color=discord.Color(0x43c6e7)
    )
    await channel.send(embed=embed)