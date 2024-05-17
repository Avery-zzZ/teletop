if __name__ == "__main__":
    from sqlalchemy_utils import database_exists
    from config import settings
    
    if not database_exists(settings['DATABASE']['url']):
        from sqlalchemy import create_engine
        from db.dao.base import Base
        from db.dao.channel import Channel
        from db.dao.message import Message
        
        engine = create_engine(
            settings['DATABASE']['url'],
            echo=True
        )
        Base.metadata.create_all(engine)