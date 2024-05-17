import re
import shlex
import logging
import traceback
import sys

from telethon import TelegramClient
from telethon.events import NewMessage, CallbackQuery
from telethon.tl.custom.message import Message

from app.app_service import AppService

logger = logging.getLogger("teletop")

def get_command_straight(msg: Message):
    return msg.raw_text

def get_command_from_reply_to(msg: Message):
    return msg.reply_to.quote_text

def set_controller(bot: TelegramClient, app_service: AppService):
    @bot.on(NewMessage(pattern=r'^/ping(\s+\S+)*$'))
    async def handler(msg: Message):
        await app_service.ping(msg, msg.raw_text)
        
    @bot.on(NewMessage(pattern=r'^/subscr_add(\s+\S+)*$'))
    async def handler(msg: Message):
        await app_service.add_subscr(msg, msg.raw_text)
        
    @bot.on(NewMessage(pattern=r'^/subscr_rm(\s+\S+)*$'))
    async def handler(msg: Message):
        await app_service.rm_subscr(msg)
        
    @bot.on(NewMessage(pattern=r'^/subscr_status(\s+\S+)*$'))
    async def handler(msg: Message):
        await app_service.check_subscr_status(msg)
        
    @bot.on(NewMessage(pattern=r'^/subscr_list(\s+\S+)*$'))
    async def handler(msg: Message):
        await app_service.list_subscr(msg)
        
    @bot.on(NewMessage(pattern=r'^/top(\s+\S+)*$'))
    async def handler(msg: Message):
        await app_service.list_top_msgs(msg, msg.raw_text)
        
    @bot.on(NewMessage(pattern=r'^/recent_top(\s+\S+)*$'))
    async def handler(msg: Message):
        await app_service.list_recent_tops(msg, msg.raw_text)
        
    @bot.on(CallbackQuery(data=re.compile(b'^/top(\s+\S+)*$')))
    async def handler(event: CallbackQuery.Event):
        try:
            data_bytes: bytes = event.data
            data_str = data_bytes.decode()
            command_append = ' '.join(shlex.split(data_str)[1:])
            msg: Message = await event.get_message()
            raw_command = ' '.join(['/top', msg.raw_text.split('\n', 1)[0], command_append])
            
            await app_service.list_top_msgs(event, raw_command)
        except Exception as e:
            no_trace_back = e.no_trace_back
            if no_trace_back is not None:
                if no_trace_back == True:
                    return
            traceback.print_exception(sys.exc_info())
        
    