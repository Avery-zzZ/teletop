if __name__ == "__main__":
    from sqlalchemy import create_engine

    from base import Base
    from channel import Channel
    from message import Message

    import sys
    from pathlib import Path
    parent_dir = Path(__file__).resolve().parent.parent.parent
    sys.path.append(str(parent_dir))
    from config import settings
    
    engine = create_engine(
        settings.database.url,
        echo=True
    )
    Base.metadata.create_all(engine)