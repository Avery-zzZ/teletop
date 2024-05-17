import logging
from typing import List, Tuple
from datetime import datetime, timezone
from queue import PriorityQueue

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from telethon import TelegramClient
from telethon.hints import EntitiesLike, Entity
from telethon.tl.types import Channel, Message
from telethon.client.messages import _MessagesIter, _IDsIter
from sqlalchemy import func

from .db import DB
from db import Channel as _Channel, Message as _Message
from .const import INIT_PROGRESS
from .tg import TelegramLimit
from util import PQItem, get_not_neg_react_num, get_msg_text


class MessageService:
    db: DB
    tg_client: TelegramClient

    logger = logging.getLogger("teletop")

    def __init__(self, db: DB, tg_client: TelegramClient) -> None:
        self.db = db
        self.tg_client = tg_client

    async def get_messages(
        self,
        entities_like: EntitiesLike,
        year: int | None,
        month: int | None,
        page: int,
    ) -> Tuple[List[_Message], int]:

        channel = await self.get_channel(entities_like)

        with self.db.newSession() as session:

            stmt = select(_Channel).where(_Channel.tg_id == channel.id)
            db_chan = session.scalar(stmt)
            if db_chan is None:
                e = ValueError(
                    f"Channel '{channel.username}'(id = {channel.id}) is not subcribed."
                )
                e.no_trace_back = True
                raise e

            start_datetime = INIT_PROGRESS
            end_datetime = db_chan.progress.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            last_month_1st = datetime(
                now.year, now.month, 1, tzinfo=timezone.utc
            ) - relativedelta(months=1)

            if year is not None:
                if month is None:
                    start_datetime = start_datetime.replace(year=year)
                    next_year = start_datetime + relativedelta(years=1)
                    end_datetime = (
                        next_year if next_year < end_datetime else end_datetime
                    )
                else:
                    start_datetime = start_datetime.replace(year=year, month=month)
                    next_month = start_datetime + relativedelta(months=1)
                    end_datetime = (
                        next_month if next_month < end_datetime else end_datetime
                    )

            if start_datetime > last_month_1st:
                err_str = "Top Messages query time should be earlier than this month."
                MessageService.logger.info(err_str)
                e = ValueError(err_str)
                e.no_trace_back = True
                raise e

            if start_datetime >= end_datetime:
                err_str = f"Top msgs of channel '{channel.username}' are not ready yet. Please try again later."
                MessageService.logger.info(err_str)
                e = ValueError(err_str)
                e.no_trace_back = True
                raise e

            stmt = (
                select(_Message)
                .where(_Message.channel_id == channel.id)
                .where(_Message.post_datetime > start_datetime)
                .where(_Message.post_datetime < end_datetime)
            )
            count_stmt = select(func.count()).select_from(stmt.subquery())
            count = session.scalar(count_stmt)
            stmt = stmt.limit(10).offset(10 * (page - 1))
            msgs = session.scalars(stmt).all()

            return (msgs, count)

    async def get_recent_tops(
        self, entities_like: EntitiesLike, max: int
    ) -> List[_Message]:
        channel = await self.get_channel(entities_like)

        now = datetime.now(timezone.utc)
        this_month_1st = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        msgs_iter = await self.tg_iter_msg(
            entity=channel,
            offset_date=this_month_1st,
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
                if msg.reactions.results is not None:
                    prev_group_reactions = msg.reactions.results

        # Process last msg group
        if prev_group_reactions is not None:
            num = get_not_neg_react_num(prev_group_reactions)
            if num != 0:
                group_1st_msg.raw_text = prev_group_text
                msg_prio_q.put_nowait(PQItem(-num, group_1st_msg))

        qsize = msg_prio_q.qsize()
        max = qsize if qsize < max else max
        msgs: List[_Message] = []
        for _ in range(max):
            item = msg_prio_q.get_nowait()
            not_neg_react = -item.priority
            msg: Message = item.item
            text = get_msg_text(msg.raw_text)
            db_msg = _Message(
                channel_id=channel.id,
                channel_msg_id=msg.id,
                text=text,
                not_neg_reactions=not_neg_react,
                post_datetime=msg.date,
            )
            msgs.append(db_msg)
        return msgs

    async def get_channel(self, entities_like: EntitiesLike) -> Channel:
        entity = None
        try:
            entity: Entity = await self.tg_client.get_entity(entities_like)
        except Exception as e:
            err_str = None
            if isinstance(e, ValueError):
                err_str = f"Entity '{entities_like}' not found: {e}"
                MessageService.logger.info(err_str)
                e = ValueError(err_str)
                e.no_trace_back = True
                raise e
            else:
                err_str = f"Met Unknown error: {e}"
                raise Exception(err_str)

        if not isinstance(entity, Channel):
            err_str = f"Entity '{entities_like}' is not a Channel"
            MessageService.logger.info(err_str)
            e = ValueError(err_str)
            e.no_trace_back = True
            raise e

        return entity

    @TelegramLimit.request
    async def tg_iter_msg(self, *args, **kargs) -> _MessagesIter | _IDsIter:
        return self.tg_client.iter_messages(*args, **kargs)
