from typing import List, Tuple, Dict

from telethon import TelegramClient
from telethon.hints import EntitiesLike

from app.core_service import CoreService
from .db import DB
from .ping import PingService
from .update_top import UpdateTopService
from .chan import ChannelService
from .msg import MessageService
from util import newTelegramClient

class CoreServiceImpl(CoreService):
    tg_client: TelegramClient
    
    ping_service: PingService
    channel_service: ChannelService
    msg_service: MessageService
    
    update_top_servie: UpdateTopService
    
    def __init__(self, config: dict, db: DB):
        self.tg_client = newTelegramClient(config, "user")        
        self.ping_service = PingService()
        self.update_top_servie = UpdateTopService(db, self.tg_client)
        self.channel_service = ChannelService(db, self.tg_client, self.update_top_servie)
        self.msg_service = MessageService(db, self.tg_client)
        
    def ping(self) -> str:
        return self.ping_service.ping()
    
    async def subscribe_channels(self, channels: List[EntitiesLike]) -> Tuple[List[str], List[Dict[str, str]], List[str]]:
        return await self.channel_service.add_channels(channels)
    
    async def get_top_messages(self, entities_like:EntitiesLike, year: int | None, month: int | None, page: int):
        return await self.msg_service.get_messages(entities_like, year, month, page)
    
    async def get_recent_top_messages(self, entities_like: EntitiesLike, max: int):
        return await self.msg_service.get_recent_tops(entities_like, max)
    
    async def start(self):
        await self.tg_client.start()
        self.update_top_servie.start()