from abc import abstractmethod,ABC

from sqlalchemy.orm import Session

class DB(ABC):
    @abstractmethod
    def newSession(self) -> Session:
        ...