from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.credit import Credit


def get_user_credits(db: Session, user_id: int) -> list[Credit]:
    return list(db.scalars(select(Credit).where(Credit.user_id == user_id)).all())
