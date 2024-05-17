from datetime import datetime, timezone
from queue import PriorityQueue
from typing import List
import logging

from dateutil.relativedelta import relativedelta
from telethon import TelegramClient
from telethon.hints import Entity, TotalList
from telethon.tl.types import Message
from telethon.client.messages import _MessagesIter, _IDsIter
from sqlalchemy import select

from .scheduler import Excecutor
from ..db import DB
from ..tg import TelegramLimit
from db import Channel as _Channel, Message as _Message
from util import PQItem, get_not_neg_react_num, get_msg_text


class ExcecutorImpl(Excecutor):
    db: DB
    tg_client: TelegramClient
    
    logger = logging.getLogger("teletop")

    def __init__(self, db: DB, tg_client: TelegramClient):
        self.db = db
        self.tg_client = tg_client

    @TelegramLimit.request
    async def tg_iter_msg(self, *args, **kargs) -> _MessagesIter | _IDsIter:
        return self.tg_client.iter_messages(*args, **kargs)

    @TelegramLimit.request
    async def tg_get_msg(self, *args, **kargs) -> TotalList | Message | None:
        return await self.tg_client.get_messages(*args, **kargs)

    async def update_chan_to_latest(self, chan: Entity):
        db_session = self.db.newSession()
        try:
            # get chan from db
            stmt = select(_Channel).where(_Channel.tg_id == chan.id)
            db_chan = db_session.scalar(stmt)
            if db_chan == None:
                raise Exception(f"No channel with this id in DB: {chan.id}")

            # Get start/end time of msgs that will be processed this turn
            next_start_datetime = db_chan.progress.replace(day=1).replace(
                tzinfo=timezone.utc
            )
            now = datetime.now(timezone.utc)
            end_datetime = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
            # All msgs until 1st of this month have been processed, return
            if next_start_datetime >= end_datetime:
                ExcecutorImpl.logger.debug(f"All msgs before this month of channel '{chan.username}' have been processed already, ignore")
                return

            # Start processing msgs month by month after start time month
            while True:
                # Get first msg after start time recorded in db
                msgs = await self.tg_get_msg(
                    entity=chan, limit=1, offset_date=next_start_datetime, reverse=True
                )
                # If no msg posted after start time, return
                if len(msgs) == 0:
                    ExcecutorImpl.logger.debug(f"Channel '{chan.username}' has not post any messages since last update, ignore")
                    break
                # Adjust start time to the month the msg is post at
                next_start_msg: Message = msgs[0]
                next_start_datetime = datetime(
                    next_start_msg.date.year, next_start_msg.date.month, 1, tzinfo=timezone.utc
                )
                # All msgs until 1st of this month have been processed, return
                if next_start_datetime >= end_datetime:
                    ExcecutorImpl.logger.debug(f"Finish processing msgs before this month of channel '{chan.username}'")
                    break
                # Get last msg id of this month
                ExcecutorImpl.logger.debug(f"Start to process msgs posted in {next_start_datetime.year}/{next_start_datetime.month} of channel '{chan.username}'")
                next_end_datetime = next_start_datetime + relativedelta(months=1)
                msg = (await self.tg_get_msg(
                    entity=chan, limit=1, offset_date=next_end_datetime
                ))[0]
                # Get all msgs of this month
                next_end_id = msg.id + 1
                msgs_iter = await self.tg_iter_msg(
                    entity=chan,
                    offset_date=next_start_datetime,
                    max_id=next_end_id,
                    reverse=True,
                )
                # Sort all msgs by total not negtive reaction using priority queue
                msg_prio_q: PriorityQueue[PQItem] = PriorityQueue()
                # Msgs is often post as a group. All reaction is stored in the 1st msg of the group.
                prev_grouped_id: int = 0
                prev_group_text: str = ""
                prev_group_reactions = None
                group_1st_msg: Message = None
                async for msg in msgs_iter:
                    # New msg group start
                    if msg.grouped_id != prev_grouped_id or prev_grouped_id is None:
                        # Not first msg of all msgs
                        if prev_grouped_id != 0:
                            # Count not neg reactions of pre group
                            if prev_group_reactions is not None:
                                num = get_not_neg_react_num(prev_group_reactions)
                                # Ignore msg group with all neg reactions
                                if num != 0:
                                    group_1st_msg.raw_text = prev_group_text
                                    msg_prio_q.put_nowait(PQItem(-num, group_1st_msg))
                                    
                                    prev_group_text = ""
                                    prev_group_reactions = None

                        prev_grouped_id = msg.grouped_id
                        group_1st_msg = msg
                    
                    if msg.raw_text is not None:
                        if len(msg.raw_text) != 0:
                            prev_group_text = msg.raw_text
                    if msg.reactions is not None:
                        prev_group_reactions = msg.reactions.results
                        

                # Process last msg group
                num = get_not_neg_react_num(prev_group_reactions)
                if num != 0:
                    group_1st_msg.raw_text = prev_group_text
                    msg_prio_q.put_nowait(PQItem(-num, group_1st_msg))

                want_num = msg_prio_q.qsize() // 10
                if want_num > 5:
                    want_num = 5

                # Persist top messages
                persist_msgs: List[_Message] = []
                for _ in range(want_num):
                    item = msg_prio_q.get_nowait()
                    not_neg_react = -item.priority
                    msg: Message = item.item
                    text = get_msg_text(msg.raw_text)
                    persist_msg = _Message(
                        channel_id=chan.id,
                        channel_msg_id=msg.id,
                        text=text,
                        not_neg_reactions=not_neg_react,
                        post_datetime=msg.date,
                    )
                    persist_msgs.append(persist_msg)
                db_session.add_all(persist_msgs)

                next_start_datetime += relativedelta(months=1)

            # Changes to db object will be synced automatically
            db_chan.progress = end_datetime
            db_session.commit()

        except Exception as e:
            db_session.rollback()
            raise e

