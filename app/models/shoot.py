import enum

from app import db
from app.utils.datetime_utils import utc_now

user_shoots = db.Table(
    "user_shoots",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("shoot_id", db.Integer, db.ForeignKey("shoots.id"), primary_key=True),
    db.Column("attended_at", db.DateTime, default=utc_now),
)


class ShootLocation(enum.Enum):
    HALL = "Hall"
    MEADOW = "Meadow"
    WOODS = "Woods"


class Shoot(db.Model):
    __tablename__ = "shoots"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    location = db.Column(db.Enum(ShootLocation), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def __repr__(self):
        return f"<Shoot {self.date} at {self.location.value}>"
