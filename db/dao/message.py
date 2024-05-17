from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.dao.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)
    channel_msg_id: Mapped[int] = mapped_column(Integer)
    text: Mapped[Optional[str]] = mapped_column(String(255))
    not_neg_reactions: Mapped[int] = mapped_column(Integer)
    post_datetime: Mapped[datetime] = mapped_column(DateTime)

    channel: Mapped["Channel"] = relationship(
        back_populates="messages",
        foreign_keys=channel_id,
        primaryjoin="Message.channel_id == Channel.tg_id",
    )

    def __init__(
        self,
        channel_id: int,
        channel_msg_id: int,
        text: str,
        not_neg_reactions: int,
        post_datetime: datetime,
    ):
        self.channel_id = channel_id
        self.channel_msg_id = channel_msg_id
        self.text = text
        self.not_neg_reactions = not_neg_reactions
        self.post_datetime = post_datetime

    def __repr__(self) -> str:
        return f"Message(id={self.id!r}, channel_id={self.channel_id!r}, channel_msg_id={self.channel_msg_id!r}, text={self.text!r})"
