from datetime import date

from app import db
from app.models import Shoot
from app.models.shoot import ShootLocation
from app.repositories import ShootRepository


def test_shoot_repository_get_all(app):
    shoot = Shoot(date=date.today(), location=ShootLocation.HALL)
    db.session.add(shoot)
    db.session.commit()

    shoots = ShootRepository.get_all()
    assert len(shoots) >= 1
