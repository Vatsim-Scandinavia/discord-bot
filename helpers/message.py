from typing import Optional

import discord

from helpers.config import config


def embed(
    description: Optional[str] = None,
    colour=None,
    title: Optional[str] = None,
    author: Optional[dict] = None,
    url: Optional[str] = None,
    image: Optional[str] = None,
    footer: Optional[dict] = None,
    fields: Optional[list] = None,
    timestamp=None,
) -> discord.Embed:
    """
    Function returns embeded styled message
    :param title:
    :param description:
    :param colour:
    :param author:
    :param image:
    :param footer:
    :param fields:
    :param timestamp:
    :return:
    """
    if colour is None:
        colour = config.VATSCA_BLUE

    if timestamp:
        embed = discord.Embed(
            title=title,
            url=url,
            description=description,
            colour=colour,
            timestamp=timestamp,
        )
    else:
        embed = discord.Embed(
            title=title, url=url, description=description, colour=colour
        )

    if author:
        embed.set_author(
            name=author['name'], url=author['url'], icon_url=author['icon']
        )

    if image:
        embed.set_image(url=image)

    if fields:
        for field in fields:
            embed.add_field(name=field['name'], value=field['value'])

    if footer:
        embed.set_footer(text=footer['text'], icon_url=footer['icon'])

    return embed
