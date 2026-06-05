from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.utils.datetime_utils import utc_now


def get_upcoming_published_events(db: Session) -> list[Event]:
    now = utc_now()
    return list(db.scalars(select(Event).where(Event.published.is_(True), Event.start_date >= now).order_by(Event.start_date)).all())
