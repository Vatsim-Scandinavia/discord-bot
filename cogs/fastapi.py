import asyncio
import uvicorn

from fastapi import FastAPI, HTTPException, Form, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from typing import Annotated

from discord.ext import commands

from helpers.staffing_async import StaffingAsync
from helpers.api import APIHelper
from helpers.config import config

class FastAPICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.staffing_async = StaffingAsync()
        self.api_helper = APIHelper()

        # Initialize FastAPI
        self.app = FastAPI()

        self.app.add_api_route("/staffings/update", self.update_staffing, methods=["POST"], dependencies=[Depends(FastAPICog.get_token)])
        self.app.add_api_route("/staffings/setup", self.setup_staffing, methods=["POST"], dependencies=[Depends(FastAPICog.get_token)])

        self.bot.loop.create_task(self.run_fastapi())

    @staticmethod
    def get_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        if credentials.credentials != config.FASTAPI_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return credentials.credentials

    async def run_fastapi(self):
        conf = uvicorn.Config(self.app, host=config.FASTAPI_URL, port=config.FASTAPI_PORT, log_level="info")
        server = uvicorn.Server(conf)

        asyncio.create_task(server.serve())

    async def update_staffing(self, id: Annotated[int, Form()]):
        try:
            await self.staffing_async.update_staffing_message(self.bot, id)

            return {"message": "Staffing updated successfully"}
        
        except Exception as e:
            print(f"Error updating staffing: {e}")
            raise HTTPException(status_code=500, detail=f"Staffing update failed. Error: {e}")

    async def setup_staffing(self, id: Annotated[int, Form()]):
        try:
            staffing, staffing_msg = await self.staffing_async._generate_staffing_message(id)

            if not staffing or not staffing_msg:
                raise HTTPException(status_code=500, detail="Failed to generate staffing message.")

            if staffing.get('message_id'):
                raise HTTPException(status_code=500, detail="Staffing already setup")

            channel = self.bot.get_channel(int(staffing.get('channel_id', 0)))
            message = await channel.send(content=staffing_msg)
            await message.pin()

            response = await self.api_helper.patch_data(f'staffings/{id}/update', {"message_id": message.id})

            if not response:
                raise HTTPException(status_code=500, detail="Staffing setup failed.")


            return {"message": "Staffing setup successfully"}
                
        
        except Exception as e:
            print(f"Error setting up staffing: {e}")
            raise HTTPException(status_code=500, detail=f"Staffing setup failed. Error: {e}")
        
async def setup(bot):
    await bot.add_cog(FastAPICog(bot))