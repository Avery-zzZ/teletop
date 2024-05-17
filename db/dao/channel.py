from datetime import datetime
from typing import List

from sqlalchemy import String, BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.dao.base import Base


class Channel(Base):
    __tablename__ = "channels"

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    tg_username: Mapped[str] = mapped_column(String(255))
    progress: Mapped[datetime] = mapped_column(DateTime)

    messages: Mapped[List["Message"]] = relationship(
        back_populates="channel",
        foreign_keys="Message.channel_id",
        primaryjoin="Channel.tg_id == Message.channel_id"
    )
    
    def __init__(self, tg_id: int, tg_username: str, progress: datetime):
        self.tg_id = tg_id
        self.tg_username = tg_username
        self.progress = progress

    def __repr__(self) -> str:
        return f"Channel(tg_id={self.tg_id!r}, tg_username={self.tg_username!r})"
