"""Tests for mail service"""

from app.services.mail_service import (
    send_credit_purchase_receipt,
    send_password_reset,
    send_payment_receipt,
    send_welcome_email,
)


def test_send_payment_receipt_success(app, test_user, mocker):
    """Test sending payment receipt successfully"""
    mock_util_send = mocker.patch("app.utils.email.send_payment_receipt")

    from app import db
    from app.models import Payment

    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    send_payment_receipt(test_user.id, payment.id)

    # Verify the utility function was called with correct args
    assert mock_util_send.called
    call_args = mock_util_send.call_args[0]
    assert call_args[0] == test_user
    assert call_args[1].id == payment.id
    assert call_args[2] == test_user.membership


def test_send_payment_receipt_user_not_found(app, test_user, mocker, caplog):
    """Test payment receipt when user not found"""
    mock_util_send = mocker.patch("app.utils.email.send_payment_receipt")

    from app import db
    from app.models import Payment

    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    # Try to send with non-existent user
    send_payment_receipt(99999, payment.id)

    # Should not call utility function
    assert not mock_util_send.called
    # Should log error
    assert "user or payment not found" in caplog.text


def test_send_payment_receipt_payment_not_found(app, test_user, mocker, caplog):
    """Test payment receipt when payment not found"""
    mock_util_send = mocker.patch("app.utils.email.send_payment_receipt")

    # Try to send with non-existent payment
    send_payment_receipt(test_user.id, 99999)

    # Should not call utility function
    assert not mock_util_send.called
    # Should log error
    assert "user or payment not found" in caplog.text


def test_send_payment_receipt_exception_handling(app, test_user, mocker, caplog):
    """Test payment receipt handles exceptions gracefully"""
    mocker.patch("app.utils.email.send_payment_receipt", side_effect=Exception("SMTP Error"))

    from app import db
    from app.models import Payment

    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    # Should not raise exception
    send_payment_receipt(test_user.id, payment.id)

    # Should log error
    assert "Failed to send receipt email" in caplog.text


def test_send_password_reset_success(app, test_user, mocker):
    """Test sending password reset email successfully"""
    mock_mail = mocker.patch("app.mail")
    mocker.patch("flask.render_template", return_value="<html>Reset</html>")
    mocker.patch("flask.url_for", return_value="http://test.com/reset")

    send_password_reset(test_user.id, "test_token_123")

    # Verify email was sent
    assert mock_mail.send.called


def test_send_password_reset_user_not_found(app, mocker, caplog):
    """Test password reset when user not found"""
    mock_mail = mocker.patch("app.mail")

    send_password_reset(99999, "test_token")

    # Should not send email
    assert not mock_mail.send.called
    # Should log error
    assert "User 99999 not found" in caplog.text


def test_send_password_reset_exception_handling(app, test_user, mocker, caplog):
    """Test password reset handles exceptions gracefully"""
    mock_mail = mocker.patch("app.mail")
    mock_mail.send.side_effect = Exception("SMTP Error")
    mocker.patch("flask.render_template", return_value="<html>Reset</html>")
    mocker.patch("flask.url_for", return_value="http://test.com/reset")

    # Should not raise exception
    send_password_reset(test_user.id, "test_token")

    # Should log error
    assert "Failed to send password reset email" in caplog.text


def test_send_credit_purchase_receipt_success(app, test_user, mocker):
    """Test sending credit purchase receipt successfully"""
    mock_util_send = mocker.patch("app.utils.email.send_credit_purchase_receipt")

    from app import db
    from app.models import Payment

    payment = Payment(
        user_id=test_user.id,
        amount_cents=3000,
        currency="EUR",
        payment_type="credits",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    send_credit_purchase_receipt(test_user.id, payment.id, 10)

    # Verify utility was called with correct args
    assert mock_util_send.called
    # Check credits_remaining was passed
    call_args = mock_util_send.call_args[0]
    assert call_args[2] == 10  # credits_purchased
    assert call_args[3] == test_user.membership.credits_remaining()  # credits_remaining


def test_send_credit_purchase_receipt_user_not_found(app, mocker, caplog):
    """Test credit receipt when user not found"""
    mock_util_send = mocker.patch("app.utils.email.send_credit_purchase_receipt")

    send_credit_purchase_receipt(99999, 1, 10)

    # Should not call utility
    assert not mock_util_send.called
    # Should log error
    assert "user or payment not found" in caplog.text


def test_send_credit_purchase_receipt_payment_not_found(app, test_user, mocker, caplog):
    """Test credit receipt when payment not found"""
    mock_util_send = mocker.patch("app.utils.email.send_credit_purchase_receipt")

    send_credit_purchase_receipt(test_user.id, 99999, 10)

    # Should not call utility
    assert not mock_util_send.called
    # Should log error
    assert "user or payment not found" in caplog.text


def test_send_credit_purchase_receipt_no_membership(app, mocker, caplog):
    """Test credit receipt when user has no membership"""
    from app import db
    from app.models import User

    # Create user without membership
    user = User(
        name="No Membership",
        email="nomembership@test.com",
        phone="123",
        qualification="none",
    )
    user.set_password("pass")
    db.session.add(user)
    db.session.commit()

    from app.models import Payment

    payment = Payment(
        user_id=user.id,
        amount_cents=3000,
        currency="EUR",
        payment_type="credits",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    mock_util_send = mocker.patch("app.utils.email.send_credit_purchase_receipt")

    send_credit_purchase_receipt(user.id, payment.id, 10)

    # Should not call utility
    assert not mock_util_send.called
    # Should log error about no membership
    assert "has no membership" in caplog.text


def test_send_credit_purchase_receipt_exception_handling(app, test_user, mocker, caplog):
    """Test credit receipt handles exceptions gracefully"""
    mocker.patch("app.utils.email.send_credit_purchase_receipt", side_effect=Exception("Email Error"))

    from app import db
    from app.models import Payment

    payment = Payment(
        user_id=test_user.id,
        amount_cents=3000,
        currency="EUR",
        payment_type="credits",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    # Should not raise exception
    send_credit_purchase_receipt(test_user.id, payment.id, 10)

    # Should log error
    assert "Failed to send credit receipt email" in caplog.text


def test_send_welcome_email_success(app, test_user, mocker):
    """Test sending welcome email successfully"""
    mock_util_send = mocker.patch("app.utils.email.send_welcome_email")

    send_welcome_email(test_user.id)

    # Verify the utility function was called with correct user
    assert mock_util_send.called
    call_args = mock_util_send.call_args[0]
    assert call_args[0] == test_user


def test_send_welcome_email_user_not_found(app, test_user, mocker, caplog):
    """Test welcome email when user not found"""
    mock_util_send = mocker.patch("app.utils.email.send_welcome_email")

    # User ID that doesn't exist
    send_welcome_email(99999)

    # Should not call utility function
    assert not mock_util_send.called
    # Should log error
    assert "not found" in caplog.text.lower()


def test_send_welcome_email_exception_handling(app, test_user, mocker, caplog):
    """Test welcome email handles exceptions"""
    mocker.patch("app.utils.email.send_welcome_email", side_effect=Exception("Email server error"))

    send_welcome_email(test_user.id)

    # Should log the error
    assert "Failed to send welcome email" in caplog.text


def test_send_cash_payment_pending_email_success(app, test_user, mocker):
    """Test sending cash payment pending confirmation email"""
    from app import db
    from app.models import Payment
    from app.services.mail_service import send_cash_payment_pending_email

    mock_mail = mocker.patch("app.mail")

    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="cash",
        description="Annual Membership (Cash)",
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    send_cash_payment_pending_email(test_user.id, payment.id)

    assert mock_mail.send.called
    sent_message = mock_mail.send.call_args[0][0]
    assert test_user.email in sent_message.recipients
    assert "Cash Payment" in sent_message.subject


def test_send_cash_payment_pending_email_user_not_found(app, test_user, mocker, caplog):
    """Test cash payment email when user not found"""
    from app import db
    from app.models import Payment
    from app.services.mail_service import send_cash_payment_pending_email

    mock_mail = mocker.patch("app.mail")

    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="cash",
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    # Call with invalid user_id
    send_cash_payment_pending_email(99999, payment.id)

    assert not mock_mail.send.called
    assert "not found" in caplog.text.lower()


def test_send_cash_payment_pending_email_payment_not_found(app, test_user, mocker, caplog):
    """Test cash payment email when payment not found"""
    from app.services.mail_service import send_cash_payment_pending_email

    mock_mail = mocker.patch("app.mail")

    send_cash_payment_pending_email(test_user.id, 99999)

    assert not mock_mail.send.called
    assert "not found" in caplog.text.lower()


def test_send_cash_payment_pending_email_exception_handling(app, test_user, mocker, caplog):
    """Test cash payment email handles exceptions gracefully"""
    from app import db
    from app.models import Payment
    from app.services.mail_service import send_cash_payment_pending_email

    mock_mail = mocker.patch("app.mail")
    mock_mail.send.side_effect = Exception("SMTP error")

    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="cash",
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    # Should not raise
    send_cash_payment_pending_email(test_user.id, payment.id)

    assert "Failed to send cash payment pending email" in caplog.text
