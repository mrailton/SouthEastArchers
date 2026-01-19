from unittest.mock import MagicMock

from flask import get_flashed_messages, session

from app import db
from app.models import Payment
from app.services.payment_service import PaymentProcessingService


def test_finalize_and_redirect_sends_and_clears(app, test_user):
    # Create a completed payment tied to test_user
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    with app.test_request_context():
        # populate some session keys that should be cleared
        session["signup_user_id"] = test_user.id
        session["signup_payment_id"] = payment.id

        # Register a mock MailService on the app so the helper will call it
        app.extensions = getattr(app, "extensions", {})
        prev_mail = app.extensions.get("mail_service")
        try:
            mail_mock = MagicMock()
            # The real MailService has a method send_payment_receipt; ensure the mock provides it
            mail_mock.send_payment_receipt = MagicMock()
            app.extensions["mail_service"] = mail_mock

            # Call the helper
            resp = PaymentProcessingService._finalize_and_redirect(
                test_user,
                payment,
                clear_keys=("signup_user_id", "signup_payment_id"),
                flash_message="Payment complete",
                flash_category="success",
                redirect_endpoint="auth.login",
            )

            # Mail service should have been invoked
            mail_mock.send_payment_receipt.assert_called_once()

            # Session keys should have been cleared
            assert session.get("signup_user_id") is None
            assert session.get("signup_payment_id") is None

            # Flash message should be present
            messages = get_flashed_messages()
            assert "Payment complete" in messages

            # Response should be a redirect
            assert resp.status_code == 302
        finally:
            # Restore previous mail service (if any) to avoid leaking state across tests
            if prev_mail is None:
                app.extensions.pop("mail_service", None)
            else:
                app.extensions["mail_service"] = prev_mail


def test_finalize_and_redirect_skips_send_when_flag_false(app, test_user):
    payment = Payment(
        user_id=test_user.id,
        amount_cents=5000,
        currency="EUR",
        payment_type="credits",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    with app.test_request_context():
        session["credit_purchase_user_id"] = test_user.id
        session["credit_purchase_payment_id"] = payment.id

        app.extensions = getattr(app, "extensions", {})
        prev_mail = app.extensions.get("mail_service")
        try:
            mail_mock = MagicMock()
            mail_mock.send_payment_receipt = MagicMock()
            app.extensions["mail_service"] = mail_mock

            resp = PaymentProcessingService._finalize_and_redirect(
                test_user,
                payment,
                clear_keys=("credit_purchase_user_id", "credit_purchase_payment_id"),
                flash_message="Credits purchased",
                flash_category="success",
                redirect_endpoint="member.dashboard",
                send_receipt=False,
            )

            # Mail service should NOT have been called
            mail_mock.send_payment_receipt.assert_not_called()

            # Session keys cleared
            assert session.get("credit_purchase_user_id") is None
            assert session.get("credit_purchase_payment_id") is None

            # Flash message present
            messages = get_flashed_messages()
            assert "Credits purchased" in messages

            # Redirect
            assert resp.status_code == 302
        finally:
            if prev_mail is None:
                app.extensions.pop("mail_service", None)
            else:
                app.extensions["mail_service"] = prev_mail
