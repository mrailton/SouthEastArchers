from app import db
from app.models import Credit
from app.services import credits


def test_get_user_credits(app, test_user):
    db.session.add(Credit(user_id=test_user.id, amount=2, reason="Test"))
    db.session.commit()
    rows = credits.get_user_credits(test_user.id)
    assert len(rows) == 1
    assert rows[0].amount == 2
