from app.repositories.base import BaseRepository


def check_database() -> bool:
    try:
        BaseRepository.ping()
        return True
    except Exception:
        return False
