import asyncio
from abc import ABC, abstractmethod
from typing import Tuple
import logging

from telethon.hints import Entity


class Excecutor(ABC):
    @abstractmethod
    async def update_chan_to_latest(entity: Entity): ...


class Scheduler:
    chans_q: asyncio.PriorityQueue[Tuple[int, Entity]]
    logger = logging.getLogger('teletop')
    semaphore: asyncio.Queue = asyncio.Queue(5)

    excutor: Excecutor

    def __init__(self, excutor: Excecutor):
        self.excutor = excutor
        self.chans_q = asyncio.PriorityQueue()


    def plan_update_chan_soon(self, chan: Entity):
        self.plan_update_chan(chan, 0)

    def plan_update_chan(self, chan: Entity, prio: int | None = None):
        self.chans_q.put_nowait((prio, chan))
        
    async def _start_update_chan(self, chan: Entity):
        try:
            await self.excutor.update_chan_to_latest(chan)
        except Exception as e:
            # TODO
            Scheduler.logger.error(f"Met error when updating top msgs of channel '{chan.username}': {e}")
        finally:
            self.chans_q.task_done()

    async def run(self):    
        while True:
            chan = (await self.chans_q.get())[1]
            asyncio.create_task(self._start_update_chan(chan))
