"""Tests for shoot model"""

from datetime import date

from app.models import Shoot, ShootLocation, User


def test_create_shoot(app):
    from app import db

    shoot = Shoot(date=date.today(), location=ShootLocation.HALL, description="Test shoot")
    db.session.add(shoot)
    db.session.commit()

    assert shoot.id is not None
    assert shoot.location == ShootLocation.HALL
    assert shoot.date == date.today()


def test_shoot_with_attendees(app):
    """Test shoot with attendees"""
    from app import db

    shoot = Shoot(date=date.today(), location=ShootLocation.MEADOW)
    db.session.add(shoot)
    db.session.flush()

    user = User(name="Test User", email="test@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    shoot.users.append(user)
    db.session.commit()

    assert len(shoot.users) == 1
    assert shoot.users[0].name == "Test User"


def test_shoot_locations(app):
    """Test all shoot locations"""
    from app import db

    for location in [ShootLocation.HALL, ShootLocation.MEADOW, ShootLocation.WOODS]:
        shoot = Shoot(date=date.today(), location=location)
        db.session.add(shoot)

    db.session.commit()

    shoots = Shoot.query.all()
    assert len(shoots) == 3


def test_shoot_repr(app):
    """Test shoot string representation"""
    from app import db

    shoot = Shoot(date=date.today(), location=ShootLocation.HALL)
    db.session.add(shoot)
    db.session.commit()

    repr_str = repr(shoot)
    assert "Shoot" in repr_str
    assert "Hall" in repr_str  # The enum value is displayed as "Hall", not "HALL"
