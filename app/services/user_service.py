from datetime import date, timedelta

from flask import current_app, session

from app import db
from app.models import Membership, Payment, User


class UserService:

    @staticmethod
    def get_user_by_id(user_id: int) -> User | None:
        """Get a user by ID."""
        return db.session.get(User, user_id)

    @staticmethod
    def get_all_users() -> list[User]:
        """Get all users ordered by name."""
        return User.query.order_by(User.name).all()

    @staticmethod
    def update_profile(user: User, name: str = None, phone: str = None) -> tuple[bool, str]:
        """Update user profile information."""
        if name:
            user.name = name
        if phone is not None:
            user.phone = phone

        try:
            db.session.commit()
            return True, "Profile updated successfully!"
        except Exception as e:
            db.session.rollback()
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
            db.session.commit()
            return True, "Password changed successfully!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error changing password: {str(e)}")
            return False, "An error occurred while changing password."

    @staticmethod
    def create_member(
        name: str,
        email: str,
        phone: str = None,
        password: str = "changeme123",
        is_admin: bool = False,
        create_membership: bool = False,
    ) -> tuple[User | None, str | None]:
        """Create a new member (admin function)."""
        if User.query.filter_by(email=email).first():
            return None, "Email already registered."

        user = User(
            name=name,
            email=email,
            phone=phone,
            is_admin=is_admin,
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.flush()

            if create_membership:
                membership = Membership(
                    user_id=user.id,
                    start_date=date.today(),
                    expiry_date=date.today() + timedelta(days=365),
                    credits=20,
                    status="active",
                )
                db.session.add(membership)

            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating member: {str(e)}")
            return None, "An error occurred while creating member."

    @staticmethod
    def update_member(
        user: User,
        name: str,
        email: str,
        phone: str = None,
        is_admin: bool = False,
        is_active: bool = True,
        password: str = None,
        membership_start_date: date = None,
        membership_expiry_date: date = None,
        membership_credits: int = None,
    ) -> tuple[bool, str]:
        """Update an existing member (admin function)."""
        user.name = name
        user.email = email
        user.phone = phone
        user.is_admin = is_admin
        user.is_active = is_active

        if password:
            user.set_password(password)

        if user.membership:
            if membership_start_date:
                user.membership.start_date = membership_start_date
            if membership_expiry_date:
                user.membership.expiry_date = membership_expiry_date
            if membership_credits is not None:
                user.membership.credits = membership_credits

        try:
            db.session.commit()
            return True, f"Member {user.name} updated successfully!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating member: {str(e)}")
            return False, "An error occurred while updating member."

    @staticmethod
    def create_user(
        name: str,
        email: str,
        password: str,
        phone: str = None,
        qualification: str = "None",
    ) -> tuple[User | None, str | None]:
        if User.query.filter_by(email=email).first():
            return None, "Email already registered."

        from flask import current_app

        user = User(
            name=name,
            email=email,
            phone=phone,
            qualification=qualification,
            is_active=False,
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user: {str(e)}")
            return None, "An error occurred during registration."

    @staticmethod
    def authenticate(email: str, password: str) -> User | None:
        user = User.query.filter_by(email=email).first()
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
        db.session.commit()

        return True, "Password reset successfully."

    @staticmethod
    def initiate_online_payment(user: User, user_name: str) -> dict:
        from app.services import PaymentService

        payment = Payment.query.filter_by(user_id=user.id, payment_type="membership").first()
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
