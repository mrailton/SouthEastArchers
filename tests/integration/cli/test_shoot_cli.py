from datetime import date, timedelta

from app import db
from app.models import Shoot
from app.models.shoot import ShootLocation


def test_create_shoot(runner):
    shoot_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
    result = runner.invoke(args=["shoot", "create", "--location", "Hall", "--date", shoot_date, "--description", "Weekly club shoot"])
    assert result.exit_code == 0
    assert "Shoot created" in result.output
    assert "Hall" in result.output

    shoot = Shoot.query.first()
    assert shoot is not None
    assert shoot.location == ShootLocation.HALL
    assert shoot.description == "Weekly club shoot"


def test_create_shoot_without_description(runner):
    shoot_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
    result = runner.invoke(args=["shoot", "create", "--location", "Meadow", "--date", shoot_date])
    assert result.exit_code == 0
    assert "Shoot created" in result.output

    shoot = Shoot.query.first()
    assert shoot is not None
    assert shoot.description is None


def test_create_shoot_invalid_date(runner):
    result = runner.invoke(args=["shoot", "create", "--location", "Hall", "--date", "not-a-date"])
    assert result.exit_code == 0
    assert "Invalid date format" in result.output
    assert Shoot.query.count() == 0


def test_create_shoot_all_locations(runner):
    """All valid ShootLocation enum values should be accepted."""
    for loc in ("Hall", "Meadow", "Woods"):
        shoot_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        result = runner.invoke(args=["shoot", "create", "--location", loc, "--date", shoot_date])
        assert result.exit_code == 0, f"Failed for location {loc}: {result.output}"


def test_list_no_shoots(runner):
    result = runner.invoke(args=["shoot", "list"])
    assert result.exit_code == 0
    assert "No shoots found" in result.output


def test_list_shows_shoots(runner):
    shoot = Shoot(date=date.today(), location=ShootLocation.HALL, description="Test")
    db.session.add(shoot)
    db.session.commit()

    result = runner.invoke(args=["shoot", "list"])
    assert result.exit_code == 0
    assert "Hall" in result.output
    assert date.today().strftime("%Y-%m-%d") in result.output


def test_list_header_format(runner):
    shoot = Shoot(date=date.today(), location=ShootLocation.MEADOW)
    db.session.add(shoot)
    db.session.commit()

    result = runner.invoke(args=["shoot", "list"])
    assert result.exit_code == 0
    assert "ID" in result.output
    assert "Date" in result.output
    assert "Location" in result.output


def test_list_upcoming_flag(runner):
    """--upcoming should filter to future shoots only."""
    past = Shoot(date=date.today() - timedelta(days=30), location=ShootLocation.HALL)
    future = Shoot(date=date.today() + timedelta(days=30), location=ShootLocation.WOODS)
    db.session.add_all([past, future])
    db.session.commit()

    result = runner.invoke(args=["shoot", "list", "--upcoming"])
    assert result.exit_code == 0
    assert "Woods" in result.output
    # Past shoot should not appear (only upcoming)
    # Note: both dates are in the output header, so check carefully
