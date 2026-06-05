from collections.abc import AsyncGenerator

from sqlalchemy.orm import Session

from app.db import db as database
from app.db import init_db, reset_current_session, set_current_session


async def get_db() -> AsyncGenerator[Session]:
    """Open a request-scoped session.

    Does not auto-commit on success: services must call ``BaseRepository.save()``
    or ``with BaseRepository.transaction()`` so writes are persisted explicitly.
    """
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
