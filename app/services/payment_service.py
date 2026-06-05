import logging
from datetime import date
from typing import Any

from app.enums import PaymentMethod, PaymentType
from app.events import cash_payment_submitted, credit_purchased, payment_completed
from app.models import Credit, Membership, Payment, User
from app.repositories import CreditRepository, MembershipRepository, PaymentRepository, UserRepository
from app.services.result import ServiceResult
from app.services.settings_service import SettingsService
from app.services.sumup_service import SumUpService

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, processor: Any = None) -> None:
        self.processor = processor or SumUpService()

    def create_checkout(self, amount_cents: int, description: str) -> dict[str, Any] | None:
        return self.processor.create_checkout(
            amount=amount_cents,
            currency="EUR",
            description=description,
        )

    def initiate_membership_payment(self, user: User) -> ServiceResult[dict]:
        """Create payment record and SumUp checkout for membership renewal.

        On success, ``result.data`` contains::

            {"checkout_id": str, "payment_id": int, "amount": float, "description": str}
        """
        amount_cents: int = SettingsService.get("annual_membership_cost")
        description = f"Annual Membership - {user.name}"

        payment = Payment(
            user_id=user.id,
            amount_cents=amount_cents,
            currency="EUR",
            payment_type=PaymentType.MEMBERSHIP,
            payment_method=PaymentMethod.ONLINE,
            description=description,
            status="pending",
        )
        PaymentRepository.add(payment)
        PaymentRepository.save()

        checkout = self.create_checkout(amount_cents=amount_cents, description=description)

        if checkout:
            return ServiceResult.ok(
                data={
                    "checkout_id": checkout.get("id"),
                    "payment_id": payment.id,
                    "user_id": user.id,
                    "amount": amount_cents / 100.0,
                    "description": description,
                }
            )
        else:
            PaymentRepository.delete(payment)
            PaymentRepository.save()
            return ServiceResult.fail("Error creating payment. Please try again.")

    def initiate_credit_purchase(self, user: User, quantity: int) -> ServiceResult[dict]:
        """Create payment record and SumUp checkout for credit purchase.

        On success, ``result.data`` contains::

            {"checkout_id": str, "payment_id": int, "user_id": int, "quantity": int, "amount": float, "description": str}
        """
        amount_cents: int = quantity * SettingsService.get("additional_shoot_cost")
        description = f"{quantity} credits - {user.name}"

        payment = Payment(
            user_id=user.id,
            amount_cents=amount_cents,
            currency="EUR",
            payment_type=PaymentType.CREDITS,
            payment_method=PaymentMethod.ONLINE,
            description=f"{quantity} shooting credits",
            status="pending",
        )
        PaymentRepository.add(payment)
        PaymentRepository.save()

        checkout = self.create_checkout(amount_cents=amount_cents, description=description)

        if checkout:
            return ServiceResult.ok(
                data={
                    "checkout_id": checkout.get("id"),
                    "payment_id": payment.id,
                    "user_id": user.id,
                    "quantity": quantity,
                    "amount": amount_cents / 100.0,
                    "description": description,
                }
            )
        else:
            PaymentRepository.delete(payment)
            PaymentRepository.save()
            return ServiceResult.fail("Error creating payment. Please try again.")

    @staticmethod
    def initiate_cash_membership_payment(user: User) -> ServiceResult[dict]:
        """Create pending cash payment record for membership.

        On success, ``result.data`` contains::

            {"payment_id": int, "amount": float, "instructions": str}
        """
        amount_cents: int = SettingsService.get("annual_membership_cost")

        payment = Payment(
            user_id=user.id,
            amount_cents=amount_cents,
            currency="EUR",
            payment_type=PaymentType.MEMBERSHIP,
            payment_method=PaymentMethod.CASH,
            description=f"Annual Membership (Cash) - {user.name}",
            status="pending",
        )
        PaymentRepository.add(payment)
        PaymentRepository.save()

        # Emit event — handler sends confirmation email
        try:
            cash_payment_submitted.send(user_id=user.id, payment_id=payment.id)
        except Exception as e:
            logger.error(f"Failed to emit cash_payment_submitted event: {e}")

        return ServiceResult.ok(
            data={
                "payment_id": payment.id,
                "amount": amount_cents / 100.0,
                "instructions": SettingsService.get("cash_payment_instructions"),
            }
        )

    @staticmethod
    def initiate_cash_credit_purchase(user: User, quantity: int) -> ServiceResult[dict]:
        """Create pending cash payment record for credit purchase.

        On success, ``result.data`` contains::

            {"payment_id": int, "quantity": int, "amount": float, "instructions": str}
        """
        amount_cents: int = quantity * SettingsService.get("additional_shoot_cost")

        payment = Payment(
            user_id=user.id,
            amount_cents=amount_cents,
            currency="EUR",
            payment_type=PaymentType.CREDITS,
            payment_method=PaymentMethod.CASH,
            description=f"{quantity} shooting credits (Cash)",
            status="pending",
        )
        PaymentRepository.add(payment)
        PaymentRepository.save()

        # Emit event — handler sends confirmation email
        try:
            cash_payment_submitted.send(user_id=user.id, payment_id=payment.id)
        except Exception as e:
            logger.error(f"Failed to emit cash_payment_submitted event: {e}")

        return ServiceResult.ok(
            data={
                "payment_id": payment.id,
                "quantity": quantity,
                "amount": amount_cents / 100.0,
                "instructions": SettingsService.get("cash_payment_instructions"),
            }
        )

    @staticmethod
    def get_pending_cash_payment_rows() -> list[dict[str, Any]]:
        payments = PaymentRepository.get_pending_cash()
        return [{"payment": payment, "user": UserRepository.get_by_id(payment.user_id)} for payment in payments]

    @staticmethod
    def get_completed_membership_payment(user_id: int) -> Payment | None:
        return PaymentRepository.get_completed_for_user(user_id, PaymentType.MEMBERSHIP)

    @staticmethod
    def approve_cash_payment(payment_id: int) -> ServiceResult[dict[str, Any]]:
        payment = PaymentRepository.get_by_id(payment_id)
        if not payment:
            return ServiceResult.fail("Payment not found.")
        if payment.status != "pending" or payment.payment_method != PaymentMethod.CASH:
            return ServiceResult.fail("This payment cannot be approved.")

        member = UserRepository.get_by_id(payment.user_id)
        if not member:
            return ServiceResult.fail("User not found.")

        try:
            payment.mark_completed(processor="cash")
            if payment.payment_type == PaymentType.MEMBERSHIP:
                if member.membership:
                    if member.membership.status != "active":
                        member.membership.activate()
                    else:
                        expiry_date = SettingsService.calculate_membership_expiry(date.today()).date()
                        member.membership.renew(expiry_date=expiry_date)
                else:
                    expiry_date = SettingsService.calculate_membership_expiry(date.today()).date()
                    membership = Membership(
                        user_id=member.id,
                        start_date=date.today(),
                        expiry_date=expiry_date,
                        initial_credits=SettingsService.get("membership_shoots_included"),
                        purchased_credits=0,
                        status="active",
                    )
                    MembershipRepository.add(membership)
            elif payment.payment_type == PaymentType.CREDITS:
                quantity = PaymentService._credit_quantity_from_description(payment.description)
                if member.membership:
                    member.membership.add_credits(quantity)
                CreditRepository.add(Credit(user_id=member.id, amount=quantity, payment_id=payment.id))

            PaymentRepository.save()
            PaymentService._emit_payment_completed_events(payment, member)
            return ServiceResult.ok(data={"member_name": member.name}, message=f"Payment approved for {member.name}!")
        except Exception as exc:
            logger.error("Error approving payment: %s", exc)
            return ServiceResult.fail(f"Error approving payment: {exc}")

    @staticmethod
    def reject_cash_payment(payment_id: int) -> ServiceResult[dict[str, Any]]:
        payment = PaymentRepository.get_by_id(payment_id)
        if not payment:
            return ServiceResult.fail("Payment not found.")
        if payment.status != "pending" or payment.payment_method != PaymentMethod.CASH:
            return ServiceResult.fail("This payment cannot be rejected.")
        member = UserRepository.get_by_id(payment.user_id)
        payment.status = "cancelled"
        PaymentRepository.save()
        member_name = member.name if member else "user"
        return ServiceResult.ok(data={"member_name": member_name}, message=f"Payment rejected for {member_name}.")

    @staticmethod
    def _credit_quantity_from_description(description: str | None) -> int:
        if description and "shooting credits" in description.lower():
            try:
                return int(description.split()[0])
            except ValueError, IndexError:
                return 1
        return 1

    @staticmethod
    def _emit_payment_completed_events(payment: Payment, member: User) -> None:
        try:
            if payment.payment_type == PaymentType.CREDITS:
                quantity = PaymentService._credit_quantity_from_description(payment.description)
                credit_purchased.send(user_id=member.id, payment_id=payment.id, quantity=quantity)
            else:
                payment_completed.send(user_id=member.id, payment_id=payment.id, payment_type=payment.payment_type)
        except Exception:
            pass
