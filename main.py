import asyncio

from config import settings
from log import set_logger
from db import SessionFactory as DBSessionFactory
from service import CoreServiceImpl
from app import TeleTop
from init_db import create_tables_if_not_exist

async def main():
    create_tables_if_not_exist()
    set_logger(settings)
    dbSessionFactory = DBSessionFactory(settings)
    coreServiceImpl = CoreServiceImpl(settings, dbSessionFactory)
    teletop = TeleTop(settings, coreServiceImpl)
    await teletop.run()
    
if __name__ == "__main__":
    asyncio.run(main())