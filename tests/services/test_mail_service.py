from app.services.mail_service import (
    send_credit_purchase_receipt,
    send_new_member_notification,
    send_password_reset,
    send_payment_receipt,
    send_welcome_email,
)


def test_send_payment_receipt_success(app, test_user, mocker):
    mock_mail = mocker.patch("app.services.mail_service.mail")

    from app import db
    from app.models import Payment

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

    send_payment_receipt(test_user.id, payment.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients
    assert "Receipt" in msg.subject


def test_send_payment_receipt_exception_handling(app, test_user, mocker, caplog):
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("SMTP Error")

    from app import db
    from app.models import Payment

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

    send_payment_receipt(test_user.id, payment.id)

    assert "Failed to send receipt email" in caplog.text


def test_send_password_reset_success(app, test_user, mocker):
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mocker.patch("app.services.mail_service.render_template", return_value="<html>Reset</html>")
    mocker.patch("app.services.mail_service.url_for", return_value="http://test.com/reset")

    send_password_reset(test_user.id, "test_token_123")

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients
    assert "Reset" in msg.subject


def test_send_password_reset_exception_handling(app, test_user, mocker, caplog):
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("SMTP Error")
    mocker.patch("app.services.mail_service.render_template", return_value="<html>Reset</html>")
    mocker.patch("app.services.mail_service.url_for", return_value="http://test.com/reset")

    send_password_reset(test_user.id, "test_token")

    assert "Failed to send password reset email" in caplog.text


def test_send_credit_purchase_receipt_success(app, test_user, mocker):
    mock_mail = mocker.patch("app.services.mail_service.mail")

    from app import db
    from app.models import Payment

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

    send_credit_purchase_receipt(test_user.id, payment.id, 10)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients
    assert "Credit" in msg.subject


def test_send_credit_purchase_receipt_exception_handling(app, test_user, mocker, caplog):
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("Email Error")

    from app import db
    from app.models import Payment

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

    send_credit_purchase_receipt(test_user.id, payment.id, 10)

    assert "Failed to send credit receipt email" in caplog.text


def test_send_welcome_email_success(app, test_user, mocker):
    mock_mail = mocker.patch("app.services.mail_service.mail")

    send_welcome_email(test_user.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients
    assert "Welcome" in msg.subject


def test_send_welcome_email_exception_handling(app, test_user, mocker, caplog):
    mock_mail = mocker.patch("app.services.mail_service.mail")
    mock_mail.send.side_effect = Exception("Email server error")

    send_welcome_email(test_user.id)

    assert "Failed to send welcome email" in caplog.text


def test_send_cash_payment_pending_email_success(app, test_user, mocker):
    from app import db
    from app.models import Payment
    from app.services.mail_service import send_cash_payment_pending_email

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

    send_cash_payment_pending_email(test_user.id, payment.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert test_user.email in msg.recipients
    assert "Cash Payment" in msg.subject


def test_send_cash_payment_pending_email_exception_handling(app, test_user, mocker, caplog):
    from app import db
    from app.models import Payment
    from app.services.mail_service import send_cash_payment_pending_email

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

    send_cash_payment_pending_email(test_user.id, payment.id)

    assert "Failed to send cash payment pending email" in caplog.text


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


def test_send_new_member_notification_sends_to_admins(app, mocker):
    from app import db
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

    send_new_member_notification(new_user.id)

    assert mock_mail.send.called
    msg = mock_mail.send.call_args[0][0]
    assert admin1.email in msg.recipients
    assert admin2.email in msg.recipients
    assert new_user.name in msg.subject


def test_send_new_member_notification_exception_handling(app, mocker, caplog):
    from app import db
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

    send_new_member_notification(new_user.id)

    assert "Failed to send new member notification" in caplog.text
