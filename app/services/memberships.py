import logging
from datetime import date
from typing import Any

from app.enums import PaymentType
from app.events import membership_activated
from app.models import Membership, User
from app.repositories import BaseRepository, MembershipRepository, PaymentRepository
from app.services import payments, settings
from app.services.payment_fulfillment import fulfill_payment
from app.services.payment_side_effects import emit_payment_side_effects
from app.services.result import ServiceResult

logger = logging.getLogger(__name__)


def create_membership(user: User) -> ServiceResult[None]:
    if user.membership:
        return ServiceResult.fail("User already has a membership.")

    start_date = date.today()
    membership = Membership(
        user_id=user.id,
        start_date=start_date,
        expiry_date=settings.calculate_membership_expiry(start_date).date(),
        initial_credits=settings.get("membership_shoots_included"),
        purchased_credits=0,
        status="active",
    )
    try:
        MembershipRepository.add(membership)
        MembershipRepository.save()
        return ServiceResult.ok(message=f"Membership created for {user.name}.")
    except Exception as exc:
        return ServiceResult.fail(f"Error creating membership: {exc}")


def activate_membership(user: User) -> ServiceResult[dict[str, Any]]:
    if not user.membership:
        return ServiceResult.fail("No membership found.")

    if user.membership.status == "active":
        return ServiceResult.fail("Membership is already active.")

    payment_event_emitted = False
    try:
        pending_payment = PaymentRepository.get_pending_cash_for_user(user.id, PaymentType.MEMBERSHIP)
        if pending_payment:
            result = fulfill_payment(
                pending_payment,
                user,
                processor="cash",
                membership_mode="activate_or_renew",
            )
            if not result.success:
                return ServiceResult.fail(f"Error activating membership: {result.message}")
            if result.data and not result.data.already_completed:
                emit_payment_side_effects(pending_payment, user)
                payment_event_emitted = True
        else:
            with BaseRepository.transaction():
                user.membership.activate()
        return ServiceResult.ok(
            message="Membership activated successfully.",
            data={"payment_event_emitted": payment_event_emitted},
        )
    except Exception as exc:
        return ServiceResult.fail(f"Error activating membership: {exc}")


def activate_membership_for_admin(user: User) -> ServiceResult[None]:
    """Activate membership and send a receipt email when a completed payment exists."""
    result = activate_membership(user)
    if not result.success:
        return ServiceResult.fail(result.message)

    payment_event_emitted = bool(result.data and result.data.get("payment_event_emitted"))
    payment = payments.get_completed_membership_payment(user.id)
    message = f"Membership activated for {user.name}!"
    if payment and not payment_event_emitted:
        try:
            membership_activated.send(user_id=user.id, payment_id=payment.id)
            message = f"{message} Receipt email sent."
        except Exception:
            logger.exception("Failed to send membership activation receipt for user %s", user.id)

    return ServiceResult.ok(message=message)


def renew_membership(user: User) -> ServiceResult[None]:
    if not user.membership:
        return ServiceResult.fail("No membership to renew.")

    initial_credits: int = settings.get("membership_shoots_included")
    expiry_date = settings.calculate_membership_expiry(date.today()).date()
    user.membership.renew(expiry_date=expiry_date, initial_credits=initial_credits)
    try:
        MembershipRepository.save()
        return ServiceResult.ok(message="Membership renewed successfully.")
    except Exception as exc:
        return ServiceResult.fail(f"Error renewing membership: {exc}")


def deactivate_membership(user: User) -> ServiceResult[None]:
    if not user.membership:
        return ServiceResult.fail("No membership found.")

    user.membership.deactivate()
    try:
        MembershipRepository.save()
        return ServiceResult.ok(message="Membership deactivated successfully.")
    except Exception as exc:
        return ServiceResult.fail(f"Error deactivating membership: {exc}")


def get_expired_memberships() -> list[Membership]:
    return MembershipRepository.get_expired()


def expire_memberships_for_year_end() -> int:
    expired_memberships = get_expired_memberships()
    count = 0

    for membership in expired_memberships:
        membership.expire_initial_credits()
        count += 1

    if count > 0:
        MembershipRepository.save()

    return count
