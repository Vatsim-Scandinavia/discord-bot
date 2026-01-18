from typing import TypeVar, Any

import discord
from discord.ui.button import Button
import structlog
from discord import Client, Interaction, app_commands, ui
from discord.ext.commands import Bot, Cog

logger = structlog.stdlib.get_logger()

ClientT = TypeVar('ClientT', bound='Client')


class ShitHitTheFan(Exception):
    pass


class InterestPositionsSelect(ui.Select):
    def __init__(self, callback: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback_function = callback

    async def callback(self, interaction: Interaction[ClientT]) -> Any:
        await self.callback_function(interaction)


class InterestView(ui.LayoutView):
    def __init__(self, positions: list[str], staffing_view: 'StaffingView'):
        super().__init__(timeout=600)
        self.staffing_view = staffing_view
        # TODO: Make a reasonable limit of some sort
        # NOTE: Limit to 25 options per select menu
        self.positions = positions[:25]

        options = [discord.SelectOption(label=p, value=p) for p in self.positions]

        async def callback(interaction: Interaction):
            await interaction.response.defer()

        self.interested = InterestPositionsSelect(
            callback=callback,
            placeholder='Positions you are interested in',
            options=options,
            min_values=0,
            max_values=len(options),
            custom_id='interested_select',
            row=1,
        )
        self.add_item(self.interested)

        self.not_interested = InterestPositionsSelect(
            callback=callback,
            placeholder='Positions you are NOT interested in',
            options=options,
            min_values=0,
            max_values=len(options),
            custom_id='not_interested_select',
            row=2,
        )
        self.add_item(self.not_interested)

    def get_embed(self) -> discord.Embed:
        return (
            discord.Embed(
                title='Staffing Preferences',
                description=(
                    'Please select your preferences below. '
                    'This will help us assign positions based on your interests.'
                ),
            )
            .add_field(
                name='Interested',
                value='Select the positions you would like to staff.',
                inline=False,
            )
            .add_field(
                name='Not Interested',
                value='Select the positions you are NOT interested in staffing.',
                inline=False,
            )
        )

    async def on_error(
        self, interaction: Interaction, error: Exception, item: ui.Item
    ) -> None:
        logger.exception('Error in InterestView', error=str(error))
        if not interaction.response.is_done():
            await interaction.response.send_message(
                'An error occurred while processing your preferences.', ephemeral=True
            )
        await interaction.response.send_message(
            'An error occurred while processing your finished preferences.',
            ephemeral=True,
        )

    @ui.button(label='Submit Preferences', style=discord.ButtonStyle.primary, row=3)
    async def submit(self, interaction: Interaction, button: ui.Button):
        # Save preferences to the main staffing view
        self.staffing_view.user_preferences[interaction.user.id] = {
            'name': interaction.user.display_name,
            'username': str(interaction.user),
            'interested': self.interested.values,
            'not_interested': self.not_interested.values,
        }
        if interaction.message is None:
            await interaction.response.defer()
            return

        await interaction.response.edit_message(
            content=f'Your preferences have been noted.\n**Interested:** {", ".join(self.interested.values)}\n**Not Interested:** {", ".join(self.not_interested.values)}',
            view=None,
            embed=None
        )


class StaffingView(ui.LayoutView):
    def __init__(self, title: str):
        super().__init__(timeout=600)
        self.title = title
        self.positions: list[str] = []
        self.message: discord.Message | None = None
        self.user_preferences: dict[int, dict] = {}
        self.add_item(Button(label="hi"))

    async def on_error(
        self, interaction: Interaction, error: Exception, item: ui.Item
    ) -> None:
        logger.exception('Error in StaffingView', error=str(error))
        if not interaction.response.is_done():
            await interaction.response.send_message(
                'An error occurred in the staffing interface.', ephemeral=True
            )

    def _get_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f'Ad-hoc Staffing: {self.title}', color=discord.Color.blue()
        )
        if self.positions:
            embed.description = '\n'.join([f'• {p}' for p in self.positions])
        else:
            embed.description = "No positions added yet. Click 'Add Position' to start."
        return embed

    async def update_message(self):
        if self.message:
            await self.message.edit(embed=self._get_embed(), view=self)

    @ui.button(label="I'm interested", style=discord.ButtonStyle.primary)
    async def mark_interest(self, interaction: Interaction, button: ui.Button):
        if not self.positions:
            await interaction.response.send_message(
                'No positions available to select.', ephemeral=True
            )
            return

        view = InterestView(self.positions, staffing_view=self)
        await interaction.response.send_message(
            embed=view.get_embed(), view=view, ephemeral=True
        )

    @ui.button(label='Add Position', style=discord.ButtonStyle.secondary)
    async def add_position(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(PositionModal(self))

    @ui.button(label='Finish', style=discord.ButtonStyle.success)
    async def finish(self, interaction: Interaction, _: ui.Button):
        self.stop()
        for child in self.children:
            child.disabled = True

        # Print the gathered data
        print(f'--- Ad-hoc Staffing Finalized: {self.title} ---')
        print(f'Positions: {", ".join(self.positions)}')
        print('User Interests:')
        for user_id, prefs in self.user_preferences.items():
            print(f'- {prefs["name"]} ({prefs["username"]}):')
            print(f'  Interested: {", ".join(prefs["interested"])}')
            print(f'  Not Interested: {", ".join(prefs["not_interested"])}')
        print('------------------------------------------')

        embed = self._get_embed()
        embed.color = discord.Color.green()
        embed.title = f'Staffing Finalized: {self.title}'
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label='Cancel', style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: Interaction, _: ui.Button):
        self.stop()
        await interaction.response.edit_message(
            content='Staffing creation cancelled.', view=None, embed=None
        )


class PositionModal(ui.Modal, title='Add Position'):
    position = ui.TextInput(
        label='Position Name',
        placeholder='e.g. ENBR_TWR (Leave empty to finish)',
        required=False,
    )

    def __init__(self, view: StaffingView):
        super().__init__()
        self.staffing_view = view

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        logger.exception('Error in PositionModal', error=str(error))
        if not interaction.response.is_done():
            await interaction.response.send_message(
                'An error occurred while adding the position.', ephemeral=True
            )

    async def on_submit(self, interaction: Interaction[ClientT]) -> None:
        if self.position.value:
            self.staffing_view.positions.append(self.position.value)

            try:
                await self.staffing_view.update_message()
            except Exception as e:
                logger.exception('Failed to update message', error=str(e))

            # Acknowledge and close the modal.
            # The user can click "Add Position" again on the View if they wish to add more.
            await interaction.response.defer()
        else:
            await interaction.response.defer()


class _AdHocStaffer(ui.Modal):
    title_input = ui.TextInput(label='Ad-hoc staffing title')

    def __init__(self, *args, bot: Bot, **kwargs):
        self._bot = bot
        super().__init__(*args, title='Ad-hoc staffing', **kwargs)

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        logger.exception('Error in _AdHocStaffer', error=str(error))
        if not interaction.response.is_done():
            await interaction.response.send_message(
                'An error occurred while creating the staffing.', ephemeral=True
            )

    async def on_submit(self, interaction: Interaction, /) -> None:
        if interaction.channel is None:
            raise ShitHitTheFan

        view = StaffingView(title=self.title_input.value)
        await interaction.response.send_message(embed=view._get_embed(), view=view)
        view.message = await interaction.original_response()


class StafferCog(Cog):
    """
    The staffer cog is a module which allows for interactive usage of dynamic ATC
    staff scheduling. It attempts to optimize for users preferences.
    """

    _staffer = app_commands.Group(
        name='staffer',
        description='Staffer-based staffing scheduling',
    )

    def __init__(self, bot: Bot):
        self._bot = bot

    @_staffer.command(name='add', description='Add a new ad-hoc staffing')
    async def new_adhoc_staffing(self, interaction: Interaction):
        await interaction.response.send_modal(_AdHocStaffer(bot=self._bot))

    @new_adhoc_staffing.error
    async def new_adhoc_staffing_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        logger.exception('Error in staffer add command', error=str(error))
        if interaction.response.is_done():
            await interaction.followup.send(
                'An error occurred while setting up the staffing.', ephemeral=True
            )
        else:
            await interaction.response.send_message(
                'An error occurred while setting up the staffing.', ephemeral=True
            )


async def setup(bot: Bot):
    await bot.add_cog(StafferCog(bot))
