from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Model
from app.db.session import Base
from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.models.user import User

user_shoots = Table(
    "user_shoots",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("shoot_id", Integer, ForeignKey("shoots.id"), primary_key=True),
    Column("attended_at", DateTime, default=utc_now),
)


class ShootLocation(enum.Enum):
    HALL = "Hall"
    MEADOW = "Meadow"
    WOODS = "Woods"


class Shoot(Model):
    __tablename__ = "shoots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    location: Mapped[ShootLocation] = mapped_column(Enum(ShootLocation), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    users: Mapped[list[User]] = relationship("User", secondary=user_shoots, back_populates="shoots")
    visitors: Mapped[list[ShootVisitor]] = relationship("ShootVisitor", back_populates="shoot", lazy="joined", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Shoot {self.date} at {self.location.value}>"


class ShootVisitor(Model):
    __tablename__ = "shoot_visitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shoot_id: Mapped[int] = mapped_column(Integer, ForeignKey("shoots.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    club: Mapped[str] = mapped_column(String(255), nullable=False)
    affiliation: Mapped[str] = mapped_column(String(10), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    shoot: Mapped[Shoot] = relationship("Shoot", back_populates="visitors")

    def __repr__(self) -> str:
        return f"<ShootVisitor {self.name} @ shoot {self.shoot_id}>"
