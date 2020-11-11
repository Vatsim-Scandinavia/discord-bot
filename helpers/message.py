import discord

def embed(title: str, description: str, colour = None, author: dict = None, image: str = None, footer: dict = None, fields: list = None) -> discord.Embed:

    if colour is None:
        colour = 0x98FB98

    embed = discord.Embed(title=title,
                              description=description,
                              colour=colour)

    if author:
        embed.set_author(name=author['name'],
                         url=author['url'],
                         icon_url=author['icon'])

    if image:
        embed.set_image(url=image)

    if fields:
        for field in fields:
            embed.add_field(name=field['name'], value=field['value'])

    if footer:
        embed.set_footer(text=footer['text'], icon_url=footer['icon'])

    return embed