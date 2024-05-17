from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session

from service import DB

class SessionFactory(DB):
    _engine: Engine = None
    
    def __init__(self, config: dict):
        """
        Args:
        - config:
            Database config.
            {
                "DATABASE": {"url": "..."}
            }
        """
        engine_params = {}
        if config.get("env", None) == "development":
            engine_params = {
                "echo": True
            }
        self._engine = create_engine(config["DATABASE"]["url"], **engine_params)
        
    def newSession(self) -> Session:
        return Session(self._engine)