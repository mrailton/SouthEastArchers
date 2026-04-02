import os
import shutil
from datetime import date, timedelta

import pytest

from app import create_app, db
from app.models import Membership, Role, User
from app.models.rbac import seed_rbac
from tests.helpers import FakeMailer, FakeQueue

# ---------------------------------------------------------------------------
# Password-hash cache – avoid repeated bcrypt work for the same plaintext.
# The first call for each unique password goes through bcrypt; subsequent
# calls reuse the cached hash.  This is safe because check_password extracts
# the salt from the stored hash, so a shared hash still validates correctly.
# ---------------------------------------------------------------------------
_password_cache: dict[str, str] = {}
_original_set_password = User.set_password


def _fast_set_password(self, password):
    """Cache-aware set_password: computes bcrypt hash once per unique password."""
    if password not in _password_cache:
        _original_set_password(self, password)
        _password_cache[password] = self.password_hash
    else:
        self.password_hash = _password_cache[password]


# ---------------------------------------------------------------------------
# Session-scoped app + schema + RBAC seed (created once for entire test run)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def app_instance():
    """Create application instance and seed RBAC data once."""
    User.set_password = _fast_set_password

    app = create_app("testing")

    with app.app_context():
        db.create_all()
        seed_rbac(db.session)

        # Pre-warm the cache with commonly used test passwords
        from app import bcrypt

        for pw in ("password123", "adminpass"):
            _password_cache[pw] = bcrypt.generate_password_hash(pw).decode("utf-8")

        yield app

        db.session.remove()
        db.drop_all()
        db.engine.dispose()

    User.set_password = _original_set_password


# ---------------------------------------------------------------------------
# Per-test fixture – transaction rollback isolation
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def app(app_instance):
    """Provide application context with transaction rollback isolation.

    Each test runs inside a database transaction that is rolled back after
    the test finishes, avoiding the cost of DELETE-all + re-seed RBAC.
    """
    with app_instance.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        # Route every session through our transacted connection so that
        # commits become savepoint releases rather than real commits.
        SessionClass = db.session.session_factory.class_
        original_get_bind = SessionClass.get_bind
        SessionClass.get_bind = lambda self, *args, **kw: connection

        db.session.remove()  # clear stale session state

        yield app_instance

        db.session.remove()
        SessionClass.get_bind = original_get_bind
        transaction.rollback()
        connection.close()


def pytest_collection_modifyitems(items):
    """Auto-apply unit/integration/e2e markers based on test file location."""
    for item in items:
        path = str(item.fspath)
        if "/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in path:
            item.add_marker(pytest.mark.e2e)


def pytest_sessionfinish(session, exitstatus):
    """Clean up artifacts after test session finishes"""
    # Remove coverage artifacts
    if os.path.exists(".coverage"):
        os.remove(".coverage")
    if os.path.exists("htmlcov"):
        shutil.rmtree("htmlcov")
    if os.path.exists("coverage.db"):
        os.remove("coverage.db")


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user"""
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
    """Create a test admin user"""
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
    """Provide a lightweight fake queue object for tests to capture enqueued jobs."""
    return FakeQueue()


@pytest.fixture
def fake_mailer():
    """Provide a lightweight fake mailer for tests to capture sent messages."""
    fm = FakeMailer()
    # Inject into common modules so tests don't need to set it manually
    from tests.helpers import inject_fake_mailer

    inject_fake_mailer(fm)
    return fm
