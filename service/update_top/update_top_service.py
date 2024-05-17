import asyncio

from telethon import TelegramClient

from .scheduler import Scheduler
from .excecutor import ExcecutorImpl
from ..db import DB

class UpdateTopService:
    scheduler: Scheduler
    
    def __init__(self, db: DB, tg_client: TelegramClient):
        self.scheduler = Scheduler(ExcecutorImpl(db, tg_client))
        
    def start(self):
        asyncio.create_task(self.scheduler.run())