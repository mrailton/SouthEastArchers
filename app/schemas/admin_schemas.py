from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ShootSchema(BaseModel):
    date: date
    location: str = Field(pattern="^(HALL|MEADOW|WOODS)$")
    description: Optional[str] = None
    attendees: Optional[List[int]] = []


class NewsSchema(BaseModel):
    title: str = Field(min_length=5)
    summary: Optional[str] = None
    content: str = Field(min_length=20)
    published: bool = False


class EventSchema(BaseModel):
    title: str = Field(min_length=5)
    description: str = Field(min_length=1)
    start_date: datetime
    location: Optional[str] = None
    published: bool = False
