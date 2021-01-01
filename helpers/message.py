import bs4
import discord
import html2markdown

from helpers.config import ADMIN_ROLES, VATSCA_BLUE


def embed(description: str, colour=None, title: str = None, author: dict = None, image: str = None, footer: dict = None,
          fields: list = None, timestamp=None) -> discord.Embed:
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
        colour = VATSCA_BLUE

    if timestamp:
        embed = discord.Embed(title=title,
                              description=description,
                              colour=colour,
                              timestamp=timestamp)
    else:
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


def roles() -> str:
    """
    Function returns tuple of admin roles
    :return:
    """
    admin_roles = tuple(ADMIN_ROLES)
    return admin_roles


def event_description(description: str) -> str:
    """
    Function converts html to markdown message
    :param description:
    :return:
    """
    soup = bs4.BeautifulSoup(description, features='html.parser')
    return html2markdown.convert(f'{soup.get_text()}').replace("&nbsp;", " ")


def get_image(text: str) -> str:
    """
    Function gets images from given description
    :param text:
    :return:
    """
    soup = bs4.BeautifulSoup(text, features='html.parser')
    img = soup.find_all('img')
    return img[0]['src']
