from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Any

from sqlalchemy import create_engine, or_
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Query, Session, sessionmaker

from app.core.config import Settings, get_settings

_current_session: ContextVar[Session | None] = ContextVar("db_session", default=None)


class Base(DeclarativeBase):
    pass


class _QueryProperty:
    def __get__(self, obj: object | None, cls: type[Model]) -> Query:
        return get_current_session().query(cls)


class Model(Base):
    __abstract__ = True
    query = _QueryProperty()


class Database:
    def __init__(self) -> None:
        self.engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    def create_session(self) -> Session:
        if self._session_factory is None:
            init_db()
        assert self._session_factory is not None
        return self._session_factory()

    def init(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        connect_args: dict[str, Any] = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        self.engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        self._session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    @property
    def session(self) -> Session:
        return get_current_session()

    @property
    def metadata(self):
        return Base.metadata

    def or_(self, *clauses):
        return or_(*clauses)

    def create_all(self) -> None:
        if self.engine is None:
            init_db()
        assert self.engine is not None
        Base.metadata.create_all(self.engine)

    def drop_all(self) -> None:
        if self.engine is None:
            init_db()
        assert self.engine is not None
        Base.metadata.drop_all(self.engine)

    def remove(self) -> None:
        session = _current_session.get()
        if session is not None:
            session.close()


db = Database()


def init_db(settings: Settings | None = None) -> None:
    if db.engine is None:
        db.init(settings)


def get_current_session() -> Session:
    session = _current_session.get()
    if session is None:
        raise RuntimeError("No database session is active for this request.")
    return session


def set_current_session(session: Session) -> Token:
    return _current_session.set(session)


def reset_current_session(token: Token) -> None:
    _current_session.reset(token)
