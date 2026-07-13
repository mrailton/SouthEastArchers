from app.models.credit import Credit
from app.repositories import CreditRepository


def get_user_credits(user_id: int) -> list[Credit]:
    return CreditRepository.get_by_user(user_id)
