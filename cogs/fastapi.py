import asyncio
from typing import Annotated

import uvicorn
from discord.ext import commands
from fastapi import Depends, FastAPI, Form, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from helpers.api import APIHelper
from helpers.config import config
from helpers.staffing_async import StaffingAsync

# Instantiate and re-use the authorization credentials
security = HTTPBearer()


class FastAPICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.staffing_async = StaffingAsync()
        self.api_helper = APIHelper()

        # Initialize FastAPI
        self.app = FastAPI()

        self.app.add_api_route(
            '/staffings/update',
            self.update_staffing,
            methods=['POST'],
            dependencies=[Depends(FastAPICog.get_token)],
        )
        self.app.add_api_route(
            '/staffings/setup',
            self.setup_staffing,
            methods=['POST'],
            dependencies=[Depends(FastAPICog.get_token)],
        )

        self.bot.loop.create_task(self.run_fastapi())

    @staticmethod
    def get_token(
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    ):
        if credentials.credentials != config.FASTAPI_TOKEN:
            raise HTTPException(status_code=401, detail='Unauthorized')
        return credentials.credentials

    async def run_fastapi(self):
        conf = uvicorn.Config(
            self.app,
            host=config.FASTAPI_URL,
            port=config.FASTAPI_PORT,
            log_level='info',
        )
        server = uvicorn.Server(conf)

        asyncio.create_task(server.serve())

    async def update_staffing(
        self,
        id: Annotated[int, Form()],
        reset: Annotated[bool | None, Form()] = None,
    ):
        try:
            await self.staffing_async.update_staffing_message(self.bot, id, reset)

            return {'message': 'Staffing updated successfully'}

        except Exception as e:
            print(f'Error updating staffing: {e}')
            raise HTTPException(  # noqa: B904
                status_code=500, detail=f'Staffing update failed. Error: {e}'
            )

    async def setup_staffing(self, id: Annotated[int, Form()]):
        try:
            (
                staffing,
                staffing_msg,
            ) = await self.staffing_async._generate_staffing_message(id)

            if not staffing or not staffing_msg:
                raise HTTPException(
                    status_code=500, detail='Failed to generate staffing message.'
                )

            if staffing.get('message_id'):
                raise HTTPException(status_code=500, detail='Staffing already setup')

            use_threads = staffing.get('use_threads', False) or staffing.get(
                'is_thread', False
            )

            if use_threads:
                # Thread-based staffing
                parent_channel = self.bot.get_channel(
                    int(staffing.get('channel_id', 0))
                )
                if not parent_channel:
                    raise HTTPException(
                        status_code=500,
                        detail='Parent channel not found for thread creation.',
                    )

                event = staffing.get('event', {})
                thread_name = self.staffing_async._generate_thread_name(event)

                # Send initial message and create thread from it
                # This is more reliable than creating a thread directly
                initial_message = await parent_channel.send(content=staffing_msg)
                thread = await initial_message.create_thread(
                    name=thread_name,
                    auto_archive_duration=10080,  # 7 days (Discord's max)
                )

                # Send the staffing message in the thread and pin it there
                # The initial_message is in the parent channel, so we need a new message in the thread
                thread_message = await thread.send(content=staffing_msg)
                await thread_message.pin()

                # Store both message_id (from thread) and thread_id
                response = await self.api_helper.patch_data(
                    f'staffings/{id}/update',
                    {'message_id': thread_message.id, 'thread_id': thread.id},
                )
            else:
                # Channel-based staffing
                channel = self.bot.get_channel(int(staffing.get('channel_id', 0)))
                if not channel:
                    raise HTTPException(
                        status_code=500, detail='Channel not found for staffing setup.'
                    )
                message = await channel.send(content=staffing_msg)
                await message.pin()

                response = await self.api_helper.patch_data(
                    f'staffings/{id}/update', {'message_id': message.id}
                )

            if not response:
                raise HTTPException(status_code=500, detail='Staffing setup failed.')

            return {'message': 'Staffing setup successfully'}

        except Exception as e:
            print(f'Error setting up staffing: {e}')
            raise HTTPException(  # noqa: B904
                status_code=500, detail=f'Staffing setup failed. Error: {e}'
            )


async def setup(bot):
    await bot.add_cog(FastAPICog(bot))
