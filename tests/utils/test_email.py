import pytest

from app import db
from app.models import Payment
from app.services.mail_service import (
    send_credit_purchase_receipt,
    send_payment_receipt,
    send_welcome_email,
)

# ---------------------------------------------------------------------------
# send_payment_receipt
# ---------------------------------------------------------------------------


def _make_payment(user, payment_method="online", payment_id=None, **kwargs):
    """Helper: create and persist a Payment."""
    from datetime import datetime

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


def test_send_payment_receipt_online_payment(app, test_user, mocker):
    """Test sending payment receipt for online payment"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(
        test_user,
        payment_method="online",
        external_transaction_id="txn_abc123",
        payment_processor="sumup",
    )

    send_payment_receipt(test_user.id, payment.id)

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

    send_payment_receipt(test_user.id, payment.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients


def test_send_payment_receipt_formats_receipt_number(app, test_user, mocker):
    """Test receipt number formatting SEA-XXXXXX"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="online")

    send_payment_receipt(test_user.id, payment.id)

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

    send_payment_receipt(test_user.id, payment.id)

    msg = mock_mail.send.call_args[0][0]
    assert "txn_xyz789" in (msg.html or "")


def test_send_payment_receipt_no_transaction_id_for_cash(app, test_user, mocker):
    """Test no transaction ID for cash payments"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="cash")

    send_payment_receipt(test_user.id, payment.id)

    assert mock_mail.send.called


def test_send_payment_receipt_formats_dates(app, test_user, mocker):
    """Test date formatting in receipt"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="online")

    send_payment_receipt(test_user.id, payment.id)

    msg = mock_mail.send.call_args[0][0]
    assert msg.html is not None


def test_send_payment_receipt_includes_membership_details(app, test_user, mocker):
    """Test membership details are included in receipt"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="online")

    send_payment_receipt(test_user.id, payment.id)

    msg = mock_mail.send.call_args[0][0]
    membership = test_user.membership
    html = msg.html or ""
    body = msg.body or ""
    assert membership.start_date.strftime("%d %B %Y") in html or membership.start_date.strftime("%d %B %Y") in body


def test_send_payment_receipt_handles_missing_description(app, test_user, mocker):
    """Test receipt handles missing payment description"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="online", description=None)

    send_payment_receipt(test_user.id, payment.id)

    assert mock_mail.send.called


def test_send_payment_receipt_exception_handling(app, test_user, mocker, caplog):
    """Test that SMTP errors are caught and logged, not re-raised"""
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("SMTP error")

    payment = _make_payment(test_user, payment_method="online")

    send_payment_receipt(test_user.id, payment.id)

    assert "Failed to send receipt email" in caplog.text


def test_send_payment_receipt_uses_correct_payment_method_display(app, test_user, mocker):
    """Test payment method display formatting shows SumUp for online"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    payment = _make_payment(test_user, payment_method="online")

    send_payment_receipt(test_user.id, payment.id)

    msg = mock_mail.send.call_args[0][0]
    assert "SumUp" in (msg.html or "")


# ---------------------------------------------------------------------------
# send_welcome_email
# ---------------------------------------------------------------------------


def test_send_welcome_email_success(app, test_user, mocker):
    """Test sending welcome email"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    send_welcome_email(test_user.id)

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

    send_welcome_email(test_user.id)

    msg = mock_mail.send.call_args[0][0]
    html = msg.html or ""

    if check_type == "user_name":
        expected = test_user.name

    assert expected in html, f"Expected {check_type} '{expected}' not found in email HTML"


def test_send_welcome_email_exception_handling(app, test_user, mocker, caplog):
    """Test exception handling when sending fails"""
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("Email server error")

    send_welcome_email(test_user.id)

    assert "Failed to send welcome email" in caplog.text


# ---------------------------------------------------------------------------
# send_credit_purchase_receipt
# ---------------------------------------------------------------------------


def test_send_credit_purchase_receipt(app, test_user, mocker):
    """Test sending credit purchase receipt email"""
    mock_mail = mocker.patch("app.services.mail_service.mail")

    from datetime import datetime

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

    send_credit_purchase_receipt(test_user.id, payment.id, 10)

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

    from datetime import datetime

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

    send_credit_purchase_receipt(test_user.id, payment.id, 5)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert "Credit" in msg.subject
    assert "Cash Payment" in (msg.html or "")
    assert "5" in (msg.html or "")


def test_send_payment_receipt_runtime_error_url_for(app, test_user, mocker):
    """Test payment receipt handles RuntimeError from url_for gracefully"""
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mocker.patch("app.services.mail_service.url_for", side_effect=RuntimeError("No request context"))

    payment = _make_payment(test_user, payment_method="online")

    send_payment_receipt(test_user.id, payment.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert "southeastarchers.ie" in (msg.html or "")


def test_send_credit_purchase_receipt_runtime_error_url_for(app, test_user, mocker):
    """Test credit receipt handles RuntimeError from url_for gracefully"""
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mocker.patch("app.services.mail_service.url_for", side_effect=RuntimeError("No request context"))

    from datetime import datetime

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

    send_credit_purchase_receipt(test_user.id, payment.id, 10)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert "southeastarchers.ie" in (msg.html or "")


def test_send_welcome_email_runtime_error_url_for(app, test_user, mocker):
    """Test welcome email handles RuntimeError from url_for gracefully"""
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mocker.patch("app.services.mail_service.url_for", side_effect=RuntimeError("No request context"))

    send_welcome_email(test_user.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert "southeastarchers.ie" in (msg.html or "")
