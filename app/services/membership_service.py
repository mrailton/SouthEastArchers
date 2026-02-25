from datetime import date

from app.models import Membership, User
from app.repositories import MembershipRepository, PaymentRepository
from app.services.settings_service import SettingsService


class MembershipService:
    @staticmethod
    def create_membership(user: User) -> tuple[bool, str]:
        """Create a new membership for a user who doesn't have one."""
        if user.membership:
            return False, "User already has a membership."

        settings = SettingsService.get()
        start_date = date.today()
        membership = Membership(
            user_id=user.id,
            start_date=start_date,
            expiry_date=SettingsService.calculate_membership_expiry(start_date).date(),
            initial_credits=settings.membership_shoots_included,
            purchased_credits=0,
            status="active",
        )
        try:
            MembershipRepository.add(membership)
            MembershipRepository.save()
            return True, f"Membership created for {user.name}."
        except Exception as e:
            return False, f"Error creating membership: {str(e)}"

    @staticmethod
    def activate_membership(user: User) -> tuple[bool, str]:
        if not user.membership:
            return False, "No membership found."

        if user.membership.status == "active":
            return False, "Membership is already active."

        pending_payment = PaymentRepository.get_pending_cash_for_user(user.id, "membership")

        if pending_payment:
            pending_payment.mark_completed(processor="cash")

        user.membership.activate()
        try:
            MembershipRepository.save()
            return True, "Membership activated successfully."
        except Exception as e:
            return False, f"Error activating membership: {str(e)}"

    @staticmethod
    def renew_membership(user: User) -> tuple[bool, str]:
        if not user.membership:
            return False, "No membership to renew."

        settings = SettingsService.get()
        initial_credits = settings.membership_shoots_included
        user.membership.renew(initial_credits=initial_credits)
        try:
            MembershipRepository.save()
            return True, "Membership renewed successfully."
        except Exception as e:
            return False, f"Error renewing membership: {str(e)}"

    @staticmethod
    def deactivate_membership(user: User) -> tuple[bool, str]:
        if not user.membership:
            return False, "No membership found."

        user.membership.status = "inactive"
        try:
            MembershipRepository.save()
            return True, "Membership deactivated successfully."
        except Exception as e:
            return False, f"Error deactivating membership: {str(e)}"

    @staticmethod
    def get_expiring_memberships(days: int = 30) -> list[Membership]:
        return MembershipRepository.get_expiring_soon(days)

    @staticmethod
    def get_expired_memberships() -> list[Membership]:
        return MembershipRepository.get_expired()

    @staticmethod
    def expire_memberships_for_year_end() -> int:
        """Expire initial credits for memberships that have expired."""
        expired_memberships = MembershipService.get_expired_memberships()
        count = 0

        for membership in expired_memberships:
            membership.expire_initial_credits()
            count += 1

        if count > 0:
            MembershipRepository.save()

        return count
