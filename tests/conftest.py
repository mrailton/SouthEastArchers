import os
import shutil
from datetime import date, timedelta

import pytest

from app import create_app, db
from app.models import Membership, Role, User
from app.models.rbac import seed_rbac
from tests.helpers import FakeMailer, FakeQueue


@pytest.fixture(scope="session")
def app_instance(tmp_path_factory):
    """Create application instance for testing"""
    app = create_app("testing")

    # Use a temporary database file for testing
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    with app.app_context():
        db.create_all()
        seed_rbac(db.session)
        yield app
        # Clean up after all tests
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture(scope="function")
def app(app_instance):
    """Provide application context for each test"""
    with app_instance.app_context():
        seed_rbac(db.session)
        yield app_instance
        # Clean up data after each test
        db.session.rollback()  # Rollback any failed transactions
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


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
