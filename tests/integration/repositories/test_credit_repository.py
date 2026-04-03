from app.models import Credit
from app.repositories import CreditRepository


def test_credit_repository_get_by_user(app, test_user):
    credit = Credit(user_id=test_user.id, amount=5)
    CreditRepository.add(credit)
    CreditRepository.save()

    credits = CreditRepository.get_by_user(test_user.id)
    assert len(credits) >= 1
