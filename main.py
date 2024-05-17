import asyncio

from config import settings
from log import set_logger
from db import SessionFactory as DBSessionFactory
from service import CoreServiceImpl
from app import TeleTop

async def main():
    set_logger(settings)
    dbSessionFactory = DBSessionFactory(settings)
    coreServiceImpl = CoreServiceImpl(settings, dbSessionFactory)
    teletop = TeleTop(settings, coreServiceImpl)
    await teletop.run()
    
if __name__ == "__main__":
    asyncio.run(main())