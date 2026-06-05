from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Table, Text
from app.db import Model, db
from app.utils.datetime_utils import utc_now


class Setting(Model):
    """Key-value application settings."""

    __tablename__ = "setting"

    key = Column(String(128), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<Setting {self.key}={self.value!r}>"
