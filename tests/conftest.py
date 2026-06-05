import os
import shutil
from contextlib import contextmanager
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("TEST_DATABASE_URL", "sqlite://")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret")

from click.testing import CliRunner

import app.core.config  # noqa: F401 - load settings
import app.models  # noqa: F401 - register models with metadata
from app import db
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_password
from app.db import reset_current_session, set_current_session
from app.events.handlers import connect_handlers
from app.main import app as fastapi_app
from app.models import Membership, Role, User
from app.models.rbac import seed_rbac
from tests.helpers import FakeMailer, FakeQueue
from tests.http_helpers import CSRFClient, login

_password_cache: dict[str, str] = {}
_original_set_password = User.set_password


def _fast_set_password(self, password):
    if password not in _password_cache:
        _original_set_password(self, password)
        _password_cache[password] = self.password_hash
    else:
        self.password_hash = _password_cache[password]


class _TestApp:
    @contextmanager
    def app_context(self):
        yield


@pytest.fixture(scope="session")
def app_instance():
    """Create database schema and seed RBAC once per test run."""
    User.set_password = _fast_set_password

    get_settings.cache_clear()
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db.engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    db._session_factory = sessionmaker(bind=db.engine, autoflush=False, autocommit=False)
    db.create_all()
    session = db.create_session()
    token = set_current_session(session)
    seed_rbac(session)
    session.commit()
    session.close()
    reset_current_session(token)

    for pw in ("password123", "adminpass"):
        _password_cache[pw] = hash_password(pw)

    connect_handlers()

    yield _TestApp()

    db.drop_all()
    if db.engine is not None:
        db.engine.dispose()
    get_settings.cache_clear()
    User.set_password = _original_set_password


@pytest.fixture(scope="function")
def app(app_instance):
    """Transaction-isolated database session for each test."""
    from sqlalchemy import event
    from sqlalchemy.orm import sessionmaker

    connection = db.engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, autoflush=False, autocommit=False)()
    nested = connection.begin_nested()
    token = set_current_session(session)

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield app_instance

    session.close()
    reset_current_session(token)
    event.remove(session, "after_transaction_end", restart_savepoint)
    transaction.rollback()
    connection.close()


def pytest_collection_modifyitems(items):
    for item in items:
        path = str(item.fspath)
        if "/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/feature/" in path:
            item.add_marker(pytest.mark.feature)


def pytest_sessionfinish(session, exitstatus):
    if os.path.exists(".coverage"):
        os.remove(".coverage")
    if os.path.exists("htmlcov"):
        shutil.rmtree("htmlcov")
    if os.path.exists("coverage.db"):
        os.remove("coverage.db")


@pytest.fixture
def db_session(app):
    """Alias for the per-test SQLAlchemy session."""
    return db.session


@pytest.fixture
def client(app):
    session = db.session

    async def override_get_db():
        try:
            yield session
        except Exception:
            session.rollback()
            raise

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield CSRFClient(test_client)
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def runner(app):
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def test_user(app):
    user = User(
        name="Test User",
        email="test@example.com",
        phone="1234567890",
        qualification="none",
        is_active=True,
    )
    user.set_password("password123")

    membership = Membership(
        user_id=None,
        start_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=335),
        initial_credits=20,
        purchased_credits=0,
        status="active",
    )

    db.session.add(user)
    db.session.flush()

    membership.user_id = user.id
    db.session.add(membership)
    db.session.commit()

    return user


@pytest.fixture
def admin_user(app):
    user = User(
        name="Admin User",
        email="admin@example.com",
        qualification="none",
        is_active=True,
    )
    user.set_password("adminpass")
    admin_role = Role.query.filter_by(name="Admin").first()
    if admin_role:
        user.roles.append(admin_role)
    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture
def fake_queue():
    return FakeQueue()


@pytest.fixture
def fake_mailer():
    fm = FakeMailer()
    from tests.helpers import inject_fake_mailer

    inject_fake_mailer(fm)
    return fm


@pytest.fixture
def admin_client(client, admin_user):
    login(client, admin_user.email, "adminpass")
    return client


@pytest.fixture
def member_client(client, test_user):
    login(client, test_user.email, "password123")
    return client


@pytest.fixture
def member_with_credits(app, name="Test Member", email="member@example.com", initial_credits=3, purchased_credits=0, status="active"):
    user = User(name=name, email=email, phone="1234567890", is_active=True)
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=335),
        initial_credits=initial_credits,
        purchased_credits=purchased_credits,
        status=status,
    )
    db.session.add(membership)
    db.session.commit()

    return user
