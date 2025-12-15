from datetime import date, timedelta

from flask import current_app

from app import db
from app.models import Membership, Payment, User


class MembershipService:

    @staticmethod
    def activate_membership(user: User) -> tuple[bool, str]:
        if not user.membership:
            return False, "No membership found."

        if user.membership.status == "active":
            return False, "Membership is already active."

        pending_payment = Payment.query.filter_by(
            user_id=user.id,
            payment_type="membership",
            payment_method="cash",
            status="pending",
        ).first()

        if pending_payment:
            pending_payment.mark_completed()

        user.membership.activate()
        db.session.commit()

        return True, "Membership activated successfully."

    @staticmethod
    def renew_membership(user: User) -> tuple[bool, str]:
        if not user.membership:
            return False, "No membership to renew."

        user.membership.renew()
        db.session.commit()

        return True, "Membership renewed successfully."

    @staticmethod
    def deactivate_membership(user: User) -> tuple[bool, str]:
        if not user.membership:
            return False, "No membership found."

        user.membership.status = "inactive"
        db.session.commit()

        return True, "Membership deactivated successfully."

    @staticmethod
    def get_expiring_memberships(days: int = 30) -> list[Membership]:
        cutoff_date = date.today() + timedelta(days=days)
        return Membership.query.filter(Membership.status == "active", Membership.expiry_date <= cutoff_date).all()

    @staticmethod
    def get_expired_memberships() -> list[Membership]:
        return Membership.query.filter(Membership.status == "active", Membership.expiry_date < date.today()).all()
