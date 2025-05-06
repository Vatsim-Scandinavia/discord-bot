from typing import cast

import discord
import structlog
from discord import ui

from helpers.handler import Handler

logger = structlog.stdlib.get_logger()


class NicknameAssignment(ui.Modal, title='Nickname Override'):
    name = ui.TextInput(
        label='Name', placeholder='Name to display', style=discord.TextStyle.short
    )
    cid = ui.TextInput(
        label='CID', placeholder='CID', required=True, style=discord.TextStyle.short
    )
    reason = ui.TextInput(
        label='Reason',
        placeholder='Reason for the nickname override',
        required=True,
        style=discord.TextStyle.long,
    )

    def __init__(self, member: discord.Member):
        handler = Handler()
        self.member = member
        self.name.default = member.nick or ''
        try:
            cid = handler.get_cid(member)
            self.cid.default = str(cid)
        except Exception:
            logger.exception(
                'Failed to get CID', name=member.name, nick=member.nick, id=member.id
            )
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        nick = self._format_nick(self.name.value, self.cid.value)
        member = cast('discord.Member', self.member)

        if member is None:
            await interaction.followup.send(
                'Member not found or member not part of guild.', ephemeral=True
            )
            return

        await member.edit(nick=nick, reason=self.reason.value)
        await interaction.response.send_message(
            f"Thanks. Updated {self.member}'s nickname to {nick}!", ephemeral=True
        )

    def _format_nick(self, name: str, cid: str) -> str:
        return f'{name.strip()} - {cid.strip()}'
