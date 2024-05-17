from typing import List, Tuple, Dict
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from telethon import TelegramClient
from telethon.hints import EntitiesLike, Entity
from telethon.tl.types import Channel
from dateutil.relativedelta import relativedelta

from .db import DB
from .update_top import UpdateTopService
from db import Channel as _Channel, Message as _Message
from .const import INIT_PROGRESS


class ChannelService:

    db: DB
    tg_client: TelegramClient
    update_top_servie: UpdateTopService

    logger = logging.getLogger("teletop")

    def __init__(
        self, db: DB, tg_client: TelegramClient, update_top_service: UpdateTopService
    ) -> None:
        self.db = db
        self.tg_client = tg_client
        self.update_top_servie = update_top_service

    async def add_channels(
        self, channels: List[EntitiesLike]
    ) -> Tuple[List[str], List[Dict[str, str]], List[str]]:
        success_list: List[str] = []
        fail_list: List[Dict[str, str]] = []
        already_list: List[str] = []

        for username in channels:
            try:
                entity: Entity = await self.tg_client.get_entity(username)
                if not isinstance(entity, Channel):
                    _add_chan_fail(fail_list, username, "Not a channel")
                    continue

                with self.db.newSession() as session:
                    start_progress = INIT_PROGRESS
                    stmt = select(_Message).where(_Message.channel_id == entity.id).order_by(_Message.post_datetime.desc())
                    latest_msg = session.scalar(stmt)
                    if latest_msg != None:
                        post_date = latest_msg.post_datetime
                        start_progress = datetime(
                            post_date.year,
                            post_date.month,
                            1,
                            tzinfo=timezone.utc
                        ) + relativedelta(months=1)
                    chan_record = _Channel(
                        entity.id,
                        entity.username,
                        start_progress,
                    )
                    try:
                        session.add(chan_record)
                        session.commit()
                        ChannelService.logger.info(
                            f"Success adding channel: {username}"
                        )
                        success_list.append(username)
                        self.update_top_servie.scheduler.plan_update_chan_soon(entity)

                    except Exception as e:
                        # TODO
                        ChannelService.logger.debug(
                            f"Channel already exists: '{username}'"
                        )
                        already_list.append(username)
                        session.rollback()
                        continue

            except Exception as e:
                if isinstance(e, ValueError):
                    _add_chan_fail(fail_list, username, "Channel not found")
                    continue
                else:
                    ChannelService.logger.error(e)
                    _add_chan_fail(fail_list, username, "Unknown error happend")
                    continue

        return (success_list, fail_list, already_list)

def _add_chan_fail(fail_list: List[Dict[str, str]], username: str, reason: str):
    ChannelService.logger.debug(f"Add channel '{username}' fail: {reason}")
    fail_list.append({username: reason})
