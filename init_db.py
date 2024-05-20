def create_tables_if_not_exist():
    from sqlalchemy_utils import database_exists, create_database
    from config import settings
    
    if not database_exists(settings['DATABASE']['url']):
        create_database(settings['DATABASE']['url'], 'utf8mb4')
        
        from sqlalchemy import create_engine
        from db.dao.base import Base
        from db.dao.channel import Channel
        from db.dao.message import Message
        
        engine = create_engine(
            settings['DATABASE']['url'],
            echo=True
        )
        Base.metadata.create_all(engine)