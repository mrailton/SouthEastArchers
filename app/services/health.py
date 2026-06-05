from sqlalchemy import text

from app.db import get_current_session


def check_database() -> bool:
    try:
        get_current_session().execute(text("SELECT 1"))
        return True
    except Exception:
        return False
