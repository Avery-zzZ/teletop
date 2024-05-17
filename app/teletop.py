import asyncio

from telethon import TelegramClient

from app.core_service import CoreService
from app.app_service import AppService
from app.controller import set_controller
from util import newTelegramClient

class TeleTop:
    bot_client: TelegramClient
    app_service: AppService
    config: dict
    
    def __init__(self, config: dict, core_service_impl: CoreService):
        self.config = config
        self.bot_client = newTelegramClient(config, "bot")
        self.app_service = AppService(core_service_impl)
        set_controller(self.bot_client, self.app_service)
        
    async def run(self):
        await self.app_service.start()
        await self.bot_client.start(bot_token=self.config['TELEGRAM']['bot_token'])
        await self.bot_client.run_until_disconnected()
       