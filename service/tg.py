from typing import Callable
import asyncio

class TelegramLimit:
    
    semaphore: asyncio.Queue = asyncio.Queue(3)
    
    @classmethod
    def request(cls, _func: Callable):
        async def wrapper(self, *_args, **_kargs):
            await cls.semaphore.put(None)
            exception: Exception = None
            
            try:
                result = await _func(self, *_args, **_kargs)
            except Exception as e:
                exception = e
            finally:
                cls.semaphore.get_nowait()
                cls.semaphore.task_done()
                
            if exception is not None:
                raise exception
            else:
                return result
            
        return wrapper