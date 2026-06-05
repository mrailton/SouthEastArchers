from collections.abc import AsyncGenerator

from sqlalchemy.orm import Session

from app.db import db as database
from app.db import init_db, reset_current_session, set_current_session


async def get_db() -> AsyncGenerator[Session]:
    init_db()
    session = database.create_session()
    token = set_current_session(session)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        reset_current_session(token)
