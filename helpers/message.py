import re
import discord

from markdownify import markdownify as md
from helpers.config import STAFF_ROLES, VATSCA_BLUE, OBS_ROLE, GUILD_ID


def embed(description: str = None, colour=None, title: str = None, author: dict = None, url: str = None, image: str = None, footer: dict = None,
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
                              url=url,
                              description=description,
                              colour=colour,
                              timestamp=timestamp)
    else:
        embed = discord.Embed(title=title,
                              url=url,
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

def staff_roles() -> str:
    """
    Function returns tuple of staff roles
    :return:
    """
    staff_roles = tuple(STAFF_ROLES)
    return staff_roles

def is_obs(interaction: discord.Interaction) -> str:
    """
    Function returns tuple of controller roles
    :return:
    """
    obs_role = discord.utils.get(interaction.guild.roles, id=OBS_ROLE)
    if obs_role in interaction.user.roles:
        raise discord.app_commands.AppCommandError('You do not have the proper roles to use this command')
    else:
        return True


def event_description(description: str) -> str:
    """
    Function converts html to markdown message
    :param description:
    :return:
    """
    
    # Create markdown of the description, except img tag and trim the result.
    markdown = md(description, strip=['img']).strip()

    # If there's more than two newlines, replace them with two, this removes excessive newlines from last step
    markdown = re.sub('\n\n(\n)*', '\n\n', markdown)

    return markdown


def get_image(text: str) -> str:
    """
    Function gets images from given description
    :param text:
    :return:
    """


    # Process the text and only convert the image
    markdown = md(text, convert=['img'])

    # Regex the URL of the image from the markdown
    img = re.findall('(?:!\[(?:.*?)\]\((.*)\))', markdown)

    # If image is found, return the first or return null
    if len(img) > 0:

        img = img[0]

        # In case of title atribute remove everything after and including whitespace
        img = img.split(' ')[0]

        return img

    return ''
