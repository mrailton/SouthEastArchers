from datetime import date

from app.models import Shoot
from app.repositories import ShootRepository, UserRepository


class ShootService:
    @staticmethod
    def create_shoot(
        shoot_date: date,
        location: str,
        description: str = None,
        attendee_ids: list[int] = None,
    ) -> tuple[Shoot | None, list[str]]:
        warnings = []
        shoot = Shoot(date=shoot_date, location=location, description=description)
        ShootRepository.add(shoot)

        try:
            ShootRepository.flush()

            if attendee_ids:
                for user_id in attendee_ids:
                    user = UserRepository.get_by_id(user_id)
                    if user and user.membership:
                        if user.membership.use_credit(allow_negative=True):
                            shoot.users.append(user)
                            total_credits = user.membership.credits_remaining()
                            if total_credits < 0:
                                warnings.append(f"{user.name} now has {total_credits} credits (negative balance).")
                        else:
                            warnings.append(f"{user.name} cannot be added (inactive membership).")

            ShootRepository.save()
            return shoot, warnings
        except Exception as e:
            return None, [f"Error creating shoot: {str(e)}"]

    @staticmethod
    def update_shoot(
        shoot: Shoot,
        shoot_date: date,
        location: str,
        description: str = None,
        attendee_ids: list[int] = None,
    ) -> tuple[bool, list[str]]:
        warnings = []
        new_attendee_ids = set(attendee_ids or [])
        old_attendee_ids = {u.id for u in shoot.users}

        removed_ids = old_attendee_ids - new_attendee_ids
        for user_id in removed_ids:
            user = UserRepository.get_by_id(user_id)
            if user and user.membership:
                user.membership.add_credits(1)

        added_ids = new_attendee_ids - old_attendee_ids
        for user_id in added_ids:
            user = UserRepository.get_by_id(user_id)
            if user and user.membership:
                if user.membership.use_credit(allow_negative=True):
                    shoot.users.append(user)
                    total_credits = user.membership.credits_remaining()
                    if total_credits < 0:
                        warnings.append(f"{user.name} now has {total_credits} credits (negative balance).")
                else:
                    warnings.append(f"{user.name} cannot be added (inactive membership).")

        shoot.users = [u for u in shoot.users if u.id in new_attendee_ids]
        shoot.date = shoot_date
        shoot.location = location
        shoot.description = description

        try:
            ShootRepository.save()
            return True, warnings
        except Exception as e:
            return False, [f"Error updating shoot: {str(e)}"]

    @staticmethod
    def get_all_shoots() -> list[Shoot]:
        """Get all shoots ordered by date descending."""
        return ShootRepository.get_all()

    @staticmethod
    def get_shoot_by_id(shoot_id: int) -> Shoot | None:
        """Get a shoot by ID."""
        return ShootRepository.get_by_id(shoot_id)

    @staticmethod
    def get_active_members_with_credits() -> list[tuple[int, str]]:
        """Get active members with their credit information for form choices."""
        active_members = UserRepository.get_active_with_membership()
        return [(u.id, f"{u.name} ({u.membership.credits_remaining()} credits)") for u in active_members if u.membership and u.membership.is_active()]
