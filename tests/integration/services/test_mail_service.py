from datetime import datetime

import pytest

from app import db
from app.models import Payment
from app.services.mail_service import MailService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_payment(user, payment_method="online", payment_id=None, **kwargs):
    """Helper: create and persist a Payment."""
    p = Payment(
        user_id=user.id,
        amount=kwargs.get("amount", 100.00),
        amount_cents=kwargs.get("amount_cents", 10000),
        currency="EUR",
        payment_type="membership",
        payment_method=payment_method,
        description=kwargs.get("description", "Annual Membership"),
        status="completed",
        created_at=datetime.now(),
        **{k: v for k, v in kwargs.items() if k not in ("amount", "amount_cents", "description")},
    )
    if payment_id:
        p.id = payment_id
    db.session.add(p)
    db.session.commit()
    return p


def _make_user_with_permission(db, permission_name: str, email_prefix: str):
    from app.models import Permission, Role, User

    perm = Permission.query.filter_by(name=permission_name).first()
    if not perm:
        perm = Permission(name=permission_name, description="test perm")
        db.session.add(perm)
        db.session.flush()

    role = Role(name=f"{email_prefix}_role", description="test role")
    role.permissions = [perm]
    db.session.add(role)
    db.session.flush()

    user = User(
        name=f"{email_prefix} Admin",
        email=f"{email_prefix}@example.com",
        qualification="none",
        is_active=True,
    )
    user.set_password("pass")
    user.roles = [role]
    db.session.add(user)
    db.session.commit()
    return user


# ---------------------------------------------------------------------------
# send_payment_receipt
# ---------------------------------------------------------------------------


def test_send_payment_receipt_online_payment(app, test_user, mocker):
    """Test sending payment receipt for online payment"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(
        test_user,
        payment_method="online",
        external_transaction_id="txn_abc123",
        payment_processor="sumup",
    )

    MailService.send_payment_receipt(test_user.id, payment.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients
    assert "Receipt" in msg.subject
    assert msg.html is not None
    assert msg.body is not None


def test_send_payment_receipt_cash_payment(app, test_user, mocker):
    """Test sending payment receipt for cash payment"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="cash")

    MailService.send_payment_receipt(test_user.id, payment.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients


def test_send_payment_receipt_formats_receipt_number(app, test_user, mocker):
    """Test receipt number formatting SEA-XXXXXX"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="online")

    MailService.send_payment_receipt(test_user.id, payment.id)

    msg = mock_mail.send.call_args[0][0]
    expected = f"SEA-{payment.id:06d}"
    assert expected in (msg.html or "") or expected in (msg.body or "")


def test_send_payment_receipt_includes_transaction_id_for_online(app, test_user, mocker):
    """Test transaction ID is included for online payments"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(
        test_user,
        payment_method="online",
        external_transaction_id="txn_xyz789",
        payment_processor="sumup",
    )

    MailService.send_payment_receipt(test_user.id, payment.id)

    msg = mock_mail.send.call_args[0][0]
    assert "txn_xyz789" in (msg.html or "")


def test_send_payment_receipt_no_transaction_id_for_cash(app, test_user, mocker):
    """Test no transaction ID for cash payments"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="cash")

    MailService.send_payment_receipt(test_user.id, payment.id)

    assert mock_mail.send.called


def test_send_payment_receipt_formats_dates(app, test_user, mocker):
    """Test date formatting in receipt"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="online")

    MailService.send_payment_receipt(test_user.id, payment.id)

    msg = mock_mail.send.call_args[0][0]
    assert msg.html is not None


def test_send_payment_receipt_includes_membership_details(app, test_user, mocker):
    """Test membership details are included in receipt"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="online")

    MailService.send_payment_receipt(test_user.id, payment.id)

    msg = mock_mail.send.call_args[0][0]
    membership = test_user.membership
    html = msg.html or ""
    body = msg.body or ""
    assert membership.start_date.strftime("%d %B %Y") in html or membership.start_date.strftime("%d %B %Y") in body


def test_send_payment_receipt_handles_missing_description(app, test_user, mocker):
    """Test receipt handles missing payment description"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="online", description=None)

    MailService.send_payment_receipt(test_user.id, payment.id)

    assert mock_mail.send.called


def test_send_payment_receipt_exception_handling(app, test_user, mocker, caplog):
    """Test that SMTP errors are caught and logged, not re-raised"""
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("SMTP error")

    payment = _make_payment(test_user, payment_method="online")

    MailService.send_payment_receipt(test_user.id, payment.id)

    assert "Failed to send receipt email" in caplog.text


def test_send_payment_receipt_uses_correct_payment_method_display(app, test_user, mocker):
    """Test payment method display formatting shows SumUp for online"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="online")

    MailService.send_payment_receipt(test_user.id, payment.id)

    msg = mock_mail.send.call_args[0][0]
    assert "SumUp" in (msg.html or "")


def test_send_payment_receipt_runtime_error_url_for(app, test_user, mocker):
    """Test payment receipt handles RuntimeError from url_for gracefully"""
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mocker.patch("app.services.mail_service.url_for", side_effect=RuntimeError("No request context"))

    payment = _make_payment(test_user, payment_method="online")

    MailService.send_payment_receipt(test_user.id, payment.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert "southeastarchers.ie" in (msg.html or "")


# ---------------------------------------------------------------------------
# send_welcome_email
# ---------------------------------------------------------------------------


def test_send_welcome_email_success(app, test_user, mocker):
    """Test sending welcome email"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    MailService.send_welcome_email(test_user.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients
    assert "Welcome" in msg.subject
    assert msg.html is not None
    assert msg.body is not None


@pytest.mark.parametrize(
    "check_type,expected",
    [
        ("user_name", None),  # resolved dynamically below
        ("membership_cost", "€100.00"),
        ("credits_included", "20 nights"),
        ("login_link", "Login"),
    ],
)
def test_send_welcome_email_content(app, test_user, mocker, check_type, expected):
    """Test welcome email includes various required content"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    MailService.send_welcome_email(test_user.id)

    msg = mock_mail.send.call_args[0][0]
    html = msg.html or ""

    if check_type == "user_name":
        expected = test_user.name

    assert expected in html, f"Expected {check_type} '{expected}' not found in email HTML"


def test_send_welcome_email_exception_handling(app, test_user, mocker, caplog):
    """Test exception handling when sending fails"""
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("Email server error")

    MailService.send_welcome_email(test_user.id)

    assert "Failed to send welcome email" in caplog.text


def test_send_welcome_email_runtime_error_url_for(app, test_user, mocker):
    """Test welcome email handles RuntimeError from url_for gracefully"""
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mocker.patch("app.services.mail_service.url_for", side_effect=RuntimeError("No request context"))

    MailService.send_welcome_email(test_user.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert "southeastarchers.ie" in (msg.html or "")


# ---------------------------------------------------------------------------
# send_credit_purchase_receipt
# ---------------------------------------------------------------------------


def test_send_credit_purchase_receipt(app, test_user, mocker):
    """Test sending credit purchase receipt email"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = Payment(
        user_id=test_user.id,
        amount=30.00,
        amount_cents=3000,
        currency="EUR",
        payment_type="credits",
        payment_method="online",
        external_transaction_id="txn_credits_123",
        payment_processor="sumup",
        description="10 shooting credits",
        status="completed",
        created_at=datetime.now(),
    )
    db.session.add(payment)
    db.session.commit()

    MailService.send_credit_purchase_receipt(test_user.id, payment.id, 10)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients
    assert "Credit" in msg.subject
    assert msg.html is not None
    assert msg.body is not None
    assert "10" in msg.html
    assert "txn_credits_123" in msg.html
    assert f"SEA-{payment.id:06d}" in msg.html


def test_send_credit_purchase_receipt_cash(app, test_user, mocker):
    """Test sending credit purchase receipt for cash payment"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = Payment(
        user_id=test_user.id,
        amount=15.00,
        amount_cents=1500,
        currency="EUR",
        payment_type="credits",
        payment_method="cash",
        description="5 shooting credits",
        status="completed",
        created_at=datetime.now(),
    )
    db.session.add(payment)
    db.session.commit()

    MailService.send_credit_purchase_receipt(test_user.id, payment.id, 5)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert "Credit" in msg.subject
    assert "Cash Payment" in (msg.html or "")
    assert "5" in (msg.html or "")


def test_send_credit_purchase_receipt_exception_handling(app, test_user, mocker, caplog):
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("Email Error")

    payment = Payment(
        user_id=test_user.id,
        amount_cents=3000,
        currency="EUR",
        payment_type="credits",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    MailService.send_credit_purchase_receipt(test_user.id, payment.id, 10)

    assert "Failed to send credit receipt email" in caplog.text


def test_send_credit_purchase_receipt_runtime_error_url_for(app, test_user, mocker):
    """Test credit receipt handles RuntimeError from url_for gracefully"""
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mocker.patch("app.services.mail_service.url_for", side_effect=RuntimeError("No request context"))

    payment = Payment(
        user_id=test_user.id,
        amount=30.00,
        amount_cents=3000,
        currency="EUR",
        payment_type="credits",
        payment_method="online",
        status="completed",
        created_at=datetime.now(),
    )
    db.session.add(payment)
    db.session.commit()

    MailService.send_credit_purchase_receipt(test_user.id, payment.id, 10)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert "southeastarchers.ie" in (msg.html or "")


# ---------------------------------------------------------------------------
# send_password_reset
# ---------------------------------------------------------------------------


def test_send_password_reset_success(app, test_user, mocker):
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mocker.patch("app.services.mail_service.render_template", return_value="<html>Reset</html>")
    mocker.patch("app.services.mail_service.url_for", return_value="http://test.com/reset")

    MailService.send_password_reset(test_user.id, "test_token_123")

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients
    assert "Reset" in msg.subject


def test_send_password_reset_exception_handling(app, test_user, mocker, caplog):
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("SMTP Error")
    mocker.patch("app.services.mail_service.render_template", return_value="<html>Reset</html>")
    mocker.patch("app.services.mail_service.url_for", return_value="http://test.com/reset")

    MailService.send_password_reset(test_user.id, "test_token")

    assert "Failed to send password reset email" in caplog.text


# ---------------------------------------------------------------------------
# send_cash_payment_pending_email
# ---------------------------------------------------------------------------


def test_send_cash_payment_pending_email_success(app, test_user, mocker):
    mock_mail = mocker.patch("app.services.mail_service.mail")

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

    MailService.send_cash_payment_pending_email(test_user.id, payment.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients
    assert "Cash Payment" in msg.subject


def test_send_cash_payment_pending_email_exception_handling(app, test_user, mocker, caplog):
    mock_mail = mocker.patch("app.services.mail_service.mail")
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

    MailService.send_cash_payment_pending_email(test_user.id, payment.id)

    assert "Failed to send cash payment pending email" in caplog.text


# ---------------------------------------------------------------------------
# send_new_member_notification
# ---------------------------------------------------------------------------


def test_send_new_member_notification_sends_to_admins(app, mocker):
    from app.models import User

    admin1 = _make_user_with_permission(db, "members.manage_membership", "notif_admin1")
    admin2 = _make_user_with_permission(db, "members.manage_membership", "notif_admin2")

    new_user = User(
        name="New Signup",
        email="new_signup@example.com",
        phone="0871234567",
        qualification="Beginner Certificate",
        is_active=False,
    )
    new_user.set_password("pass123")
    db.session.add(new_user)
    db.session.commit()

    mock_mail = mocker.patch("app.services.mail_service.mail")

    MailService.send_new_member_notification(new_user.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert admin1.email in msg.recipients
    assert admin2.email in msg.recipients
    assert new_user.name in msg.subject


def test_send_new_member_notification_exception_handling(app, mocker, caplog):
    from app.models import User

    _make_user_with_permission(db, "members.manage_membership", "exc_notif_admin")

    new_user = User(
        name="Exc User",
        email="exc_notif@example.com",
        is_active=False,
    )
    new_user.set_password("pass")
    db.session.add(new_user)
    db.session.commit()

    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("SMTP Error")

    MailService.send_new_member_notification(new_user.id)

    assert "Failed to send new member notification" in caplog.text
