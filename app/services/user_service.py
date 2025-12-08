import uuid
from datetime import date, timedelta

from flask import current_app, session

from app import db
from app.models import Membership, Payment, User


class UserService:

    @staticmethod
    def create_user(
        name: str,
        email: str,
        password: str,
        date_of_birth: date,
        phone: str = None,
        payment_method: str = "online",
    ) -> tuple[User | None, str | None]:
        if User.query.filter_by(email=email).first():
            return None, "Email already registered."

        from flask import current_app

        age = (date.today() - date_of_birth).days // 365
        base_fee = current_app.config.get("ANNUAL_MEMBERSHIP_COST", 10000)
        membership_fee_cents = base_fee // 2 if age < 18 else base_fee

        user = User(
            name=name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
        )
        user.set_password(password)

        membership = Membership(
            user=user,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status="pending" if payment_method == "cash" else "pending",
        )

        payment = Payment(
            user=user,
            amount_cents=membership_fee_cents,
            payment_type="membership",
            payment_method=payment_method,
            status="pending",
            payment_processor="sumup" if payment_method == "online" else None,
        )

        try:
            db.session.add(user)
            db.session.add(membership)
            db.session.add(payment)
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user: {str(e)}")
            return None, "An error occurred during registration."

    @staticmethod
    def authenticate(email: str, password: str) -> User | None:
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
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
