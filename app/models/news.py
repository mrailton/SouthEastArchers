from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.db import Model
from app.utils.datetime_utils import utc_now


class News(Model):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(String(500))
    published = Column(Boolean, default=False, index=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    def publish(self) -> None:
        self.published = True
        self.published_at = utc_now()

    def __repr__(self) -> str:
        return f"<News {self.title}>"
