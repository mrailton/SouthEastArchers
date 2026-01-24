from datetime import date

from app import db
from app.models import Shoot, User


class ShootService:
    @staticmethod
    def create_shoot(
        shoot_date: date,
        location: str,
        description: str = None,
        attendee_ids: list[int] = None,
    ) -> tuple[Shoot, list[str]]:
        """
        Create a new shoot with optional attendees.
        Returns the created shoot and a list of warning messages.

        Admin can add members with 0 credits if they have active memberships,
        which will put their credit balance into negative.
        """
        warnings = []

        shoot = Shoot(
            date=shoot_date,
            location=location,
            description=description,
        )
        db.session.add(shoot)
        db.session.flush()

        if attendee_ids:
            for user_id in attendee_ids:
                user = db.session.get(User, user_id)
                if user and user.membership:
                    # Allow negative credits for active memberships (admin override)
                    if user.membership.use_credit(allow_negative=True):
                        shoot.users.append(user)
                        # Warn if credits went negative
                        if user.membership.credits < 0:
                            warnings.append(f"{user.name} now has {user.membership.credits} credits (negative balance).")
                    else:
                        # This should only happen if membership is not active
                        warnings.append(f"{user.name} cannot be added (inactive membership).")

        db.session.commit()
        return shoot, warnings

    @staticmethod
    def update_shoot(
        shoot: Shoot,
        shoot_date: date,
        location: str,
        description: str = None,
        attendee_ids: list[int] = None,
    ) -> list[str]:
        """
        Update an existing shoot and manage attendee credits.
        Returns a list of warning messages.

        Admin can add members with 0 credits if they have active memberships,
        which will put their credit balance into negative.
        """
        warnings = []
        new_attendee_ids = set(attendee_ids or [])
        old_attendee_ids = {u.id for u in shoot.users}

        # Refund credits for removed attendees
        removed_ids = old_attendee_ids - new_attendee_ids
        for user_id in removed_ids:
            user = db.session.get(User, user_id)
            if user and user.membership:
                user.membership.add_credits(1)

        # Deduct credits for new attendees
        added_ids = new_attendee_ids - old_attendee_ids
        for user_id in added_ids:
            user = db.session.get(User, user_id)
            if user and user.membership:
                # Allow negative credits for active memberships (admin override)
                if user.membership.use_credit(allow_negative=True):
                    shoot.users.append(user)
                    # Warn if credits went negative
                    if user.membership.credits < 0:
                        warnings.append(f"{user.name} now has {user.membership.credits} credits (negative balance).")
                else:
                    # This should only happen if membership is not active
                    warnings.append(f"{user.name} cannot be added (inactive membership).")

        # Update the users list to only include valid attendees
        shoot.users = [u for u in shoot.users if u.id in new_attendee_ids]

        shoot.date = shoot_date
        shoot.location = location
        shoot.description = description

        db.session.commit()
        return warnings

    @staticmethod
    def get_all_shoots() -> list[Shoot]:
        """Get all shoots ordered by date descending."""
        return Shoot.query.order_by(Shoot.date.desc()).all()

    @staticmethod
    def get_shoot_by_id(shoot_id: int) -> Shoot | None:
        """Get a shoot by ID."""
        return db.session.get(Shoot, shoot_id)

    @staticmethod
    def get_active_members_with_credits() -> list[tuple[int, str]]:
        """Get active members with their credit information for form choices."""
        active_members = User.query.filter_by(is_active=True).order_by(User.name).all()
        return [(u.id, f"{u.name} ({u.membership.credits_remaining()} credits)") for u in active_members if u.membership and u.membership.is_active()]
