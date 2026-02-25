from datetime import date

from flask import current_app, session

from app.models import Membership, User
from app.repositories import MembershipRepository, PaymentRepository, RBACRepository, UserRepository
from app.services.settings_service import SettingsService


class UserService:
    @staticmethod
    def get_user_by_id(user_id: int) -> User | None:
        """Get a user by ID."""
        return UserRepository.get_by_id(user_id)

    @staticmethod
    def get_all_users() -> list[User]:
        """Get all users ordered by name."""
        return UserRepository.get_all()

    @staticmethod
    def update_profile(user: User, name: str = None, phone: str = None) -> tuple[bool, str]:
        """Update user profile information."""
        if name:
            user.name = name
        if phone is not None:
            user.phone = phone

        try:
            UserRepository.save()
            return True, "Profile updated successfully!"
        except Exception as e:
            current_app.logger.error(f"Error updating profile: {str(e)}")
            return False, "An error occurred while updating profile."

    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> tuple[bool, str]:
        """Change user password after verifying current password."""
        if not user.check_password(current_password):
            return False, "Current password is incorrect."

        if len(new_password) < 8:
            return False, "New password must be at least 8 characters long."

        user.set_password(new_password)
        try:
            UserRepository.save()
            return True, "Password changed successfully!"
        except Exception as e:
            current_app.logger.error(f"Error changing password: {str(e)}")
            return False, "An error occurred while changing password."

    @staticmethod
    def create_member(
        name: str,
        email: str,
        phone: str = None,
        password: str = "changeme123",
        role_ids: list[int] | None = None,
        create_membership: bool = False,
        qualification: str = "none",
    ) -> tuple[User | None, str | None]:
        """Create a new member (admin function)."""
        if UserRepository.get_by_email(email):
            return None, "Email already registered."

        user = User(
            name=name,
            email=email,
            phone=phone,
            qualification=qualification,
            is_active=False,
        )
        user.set_password(password)

        try:
            UserRepository.add(user)
            UserRepository.flush()

            if role_ids:
                roles = RBACRepository.get_roles_by_ids(role_ids)
                user.roles = roles  # type: ignore[assignment]

            if create_membership:
                start_date = date.today()
                membership = Membership(
                    user_id=user.id,
                    start_date=start_date,
                    expiry_date=SettingsService.calculate_membership_expiry(start_date).date(),
                    initial_credits=20,
                    purchased_credits=0,
                    status="active",
                )
                MembershipRepository.add(membership)

            UserRepository.save()
            return user, None
        except Exception as e:
            current_app.logger.error(f"Error creating member: {str(e)}")
            return None, "An error occurred while creating member."

    @staticmethod
    def update_member(
        user: User,
        name: str,
        email: str,
        phone: str = None,
        qualification: str = None,
        qualification_detail: str = None,
        role_ids: list[int] | None = None,
        is_active: bool = True,
        password: str = None,
        membership_start_date: date = None,
        membership_expiry_date: date = None,
        membership_initial_credits: int = None,
        membership_purchased_credits: int = None,
    ) -> tuple[bool, str]:
        """Update an existing member (admin function)."""
        user.name = name
        user.email = email
        user.phone = phone
        if qualification:
            user.qualification = qualification
        user.qualification_detail = None if qualification == "none" else (qualification_detail or None)
        if role_ids is not None:
            roles = RBACRepository.get_roles_by_ids(role_ids)
            user.roles = roles  # type: ignore[assignment]
        user.is_active = is_active

        if password:
            user.set_password(password)

        if user.membership:
            if membership_start_date:
                user.membership.start_date = membership_start_date
            if membership_expiry_date:
                user.membership.expiry_date = membership_expiry_date
            if membership_initial_credits is not None:
                user.membership.initial_credits = membership_initial_credits
            if membership_purchased_credits is not None:
                user.membership.purchased_credits = membership_purchased_credits

        try:
            UserRepository.save()
            return True, f"Member {user.name} updated successfully!"
        except Exception as e:
            current_app.logger.error(f"Error updating member: {str(e)}")
            return False, "An error occurred while updating member."

    @staticmethod
    def create_user(
        name: str,
        email: str,
        password: str,
        phone: str = None,
        qualification: str = "None",
        qualification_detail: str = None,
    ) -> tuple[User | None, str | None]:
        if UserRepository.get_by_email(email):
            return None, "Email already registered."

        user = User(
            name=name,
            email=email,
            phone=phone,
            qualification=qualification,
            qualification_detail=None if qualification in (None, "none", "None") else (qualification_detail or None),
            is_active=False,
        )
        user.set_password(password)

        try:
            UserRepository.add(user)
            UserRepository.save()
            return user, None
        except Exception as e:
            current_app.logger.error(f"Error creating user: {str(e)}")
            return None, "An error occurred during registration."

    @staticmethod
    def authenticate(email: str, password: str) -> User | None:
        user = UserRepository.get_by_email(email)
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def create_password_reset_token(user: User) -> str:
        return user.generate_reset_token()

    @staticmethod
    def reset_password(token: str, new_password: str) -> tuple[bool, str]:
        user = User.verify_reset_token(token, max_age=86400)

        if not user:
            return False, "Invalid or expired reset link."

        user.set_password(new_password)
        UserRepository.save()

        return True, "Password reset successfully."

    @staticmethod
    def initiate_online_payment(user: User, user_name: str) -> dict:
        from app.services import PaymentService

        payment = PaymentRepository.get_by_user_and_type(user.id, "membership")
        if not payment:
            return {"success": False, "error": "Payment record not found"}

        amount_cents = payment.amount_cents
        payment_service = PaymentService()

        checkout = payment_service.create_checkout(
            amount_cents=amount_cents,
            description=f"Annual Membership - {user_name}",
        )

        if checkout:
            session["signup_user_id"] = user.id
            session["signup_payment_id"] = payment.id
            session["checkout_amount"] = float(amount_cents / 100.0)
            session["checkout_description"] = f"Annual Membership - {user_name}"

            return {"success": True, "checkout_id": checkout.get("id")}
        else:
            return {
                "success": False,
                "error": "Error creating payment. Please contact us to complete registration.",
            }
