from abc import ABC, abstractmethod
from typing import List, Coroutine, Tuple, Dict

from telethon.hints import EntitiesLike
from telethon.tl.custom.message import Message

from db import Message as _Message

class CoreService(ABC):
    @abstractmethod
    def ping(self) -> str:
        ...
        
    @abstractmethod
    async def subscribe_channels(channels: List[EntitiesLike]) -> Tuple[List[str], List[Dict[str, str]], List[str]]:
        ...
        
    @abstractmethod
    async def get_top_messages(self, entities_like:EntitiesLike, year: int | None, month: int | None, page: int) -> Tuple[List[_Message], int]:
        ...
    
    @abstractmethod
    async def get_recent_top_messages(self, entities_like: EntitiesLike, max: int = 10) -> List[_Message]:
        ...
    
    # @abstractmethod
    # def unsubscribe_channels(channels: List[EntitiesLike]) -> str:
    #     ...
        
    # @abstractmethod
    # def check_channels_status(channels: List[EntitiesLike]) -> str:
    #     ...
        
    # @abstractmethod
    # def list_subscriptions(page: int = 1, page_size: int = 10) -> str:
    #     ...
    
    @abstractmethod
    async def start(self) -> Coroutine:
        ...