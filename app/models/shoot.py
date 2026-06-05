import enum

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from app.db import Model
from app.db.session import Base
from app.utils.datetime_utils import utc_now

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

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    location = Column(Enum(ShootLocation), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    visitors = relationship("ShootVisitor", backref="shoot", lazy="joined", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Shoot {self.date} at {self.location.value}>"


class ShootVisitor(Model):
    __tablename__ = "shoot_visitors"

    id = Column(Integer, primary_key=True)
    shoot_id = Column(Integer, ForeignKey("shoots.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    club = Column(String(255), nullable=False)
    affiliation = Column(String(10), nullable=False)  # "AI" or "IFAF"
    payment_method = Column(String(10), nullable=False)  # "sumup" or "cash"
    created_at = Column(DateTime, default=utc_now)
