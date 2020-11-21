import discord
from helpers.config import ADMIN_ROLES, VATSCA_BLUE
import html2markdown
import bs4


def embed(title: str, description: str, colour = None, author: dict = None, image: str = None, footer: dict = None, fields: list = None) -> discord.Embed:

    if colour is None:
        colour = VATSCA_BLUE

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
    admin_roles = tuple(ADMIN_ROLES)
    return admin_roles


def event_description(description: str) -> str:
    soup = bs4.BeautifulSoup(description, features='html.parser')
    return html2markdown.convert(f'{soup.get_text()}')


def get_image(text: str) -> str:
    soup = bs4.BeautifulSoup(text, features='html.parser')
    img = soup.find_all('img')
    return img[0]['src']