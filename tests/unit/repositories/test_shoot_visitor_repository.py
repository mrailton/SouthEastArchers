from datetime import date

from app.models import Shoot, ShootLocation, ShootVisitor
from app.repositories import ShootVisitorRepository


def test_get_by_shoot_id(app):
    """Test getting visitors by shoot ID"""
    from app import db

    # Create a shoot first
    shoot = Shoot(
        date=date(2026, 6, 1),
        location=ShootLocation.MEADOW,
    )
    db.session.add(shoot)
    db.session.flush()

    # Add some visitors
    v1 = ShootVisitor(shoot_id=shoot.id, name="Visitor 1", club="Test Club", affiliation="IFAF", payment_method="cash")
    v2 = ShootVisitor(shoot_id=shoot.id, name="Visitor 2", club="Test Club", affiliation="IFAF", payment_method="cash")
    db.session.add_all([v1, v2])
    db.session.commit()

    visitors = ShootVisitorRepository.get_by_shoot_id(shoot.id)
    assert len(visitors) == 2


def test_get_by_shoot_id_no_visitors(app):
    """Test getting visitors for shoot with none"""
    from app import db

    shoot = Shoot(
        date=date(2026, 6, 1),
        location=ShootLocation.HALL,
    )
    db.session.add(shoot)
    db.session.commit()

    visitors = ShootVisitorRepository.get_by_shoot_id(shoot.id)
    assert len(visitors) == 0


def test_add_visitor(app):
    """Test adding a visitor"""
    from app import db

    shoot = Shoot(
        date=date(2026, 6, 1),
        location=ShootLocation.WOODS,
    )
    db.session.add(shoot)
    db.session.flush()

    visitor = ShootVisitor(shoot_id=shoot.id, name="New Visitor", club="Test Club", affiliation="IFAF", payment_method="cash")
    ShootVisitorRepository.add(visitor)
    ShootVisitorRepository.flush()

    assert visitor.id is not None


def test_delete_visitor(app):
    """Test deleting a visitor"""
    from app import db

    shoot = Shoot(
        date=date(2026, 6, 1),
        location=ShootLocation.MEADOW,
    )
    db.session.add(shoot)
    db.session.flush()

    visitor = ShootVisitor(shoot_id=shoot.id, name="To Delete", club="Test Club", affiliation="IFAF", payment_method="cash")
    db.session.add(visitor)
    db.session.commit()

    assert visitor.id is not None
    ShootVisitorRepository.delete(visitor)
    ShootVisitorRepository.save()

    # Verify it's deleted
    visitors = ShootVisitorRepository.get_by_shoot_id(shoot.id)
    assert len(visitors) == 0
