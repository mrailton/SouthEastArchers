from unittest.mock import MagicMock, patch

import app as app_mod
from app import db
from app.models import Payment, User
from app.services.background_jobs import send_password_reset_job, send_payment_receipt_job
from app.services.mail_service import send_payment_receipt as module_send_payment_receipt
from tests.helpers import create_payment_for_user, inject_fake_mailer


def test_module_helper_transient_falls_back_to_sync_if_no_registered_and_no_task_queue(monkeypatch, app, test_user):
    payment = create_payment_for_user(db, test_user)

    with app.test_request_context():
        # Ensure no registered mail_service
        app.extensions = getattr(app, "extensions", {})
        app.extensions.pop("mail_service", None)

        # Ensure module-level task_queue is None
        monkeypatch.setattr("app.task_queue", None, raising=False)

        with patch("app.utils.email.send_payment_receipt") as mock_send:
            module_send_payment_receipt(test_user.id, payment.id)
            mock_send.assert_called_once()


def test_module_helper_outside_app_context_uses_transient_queue(monkeypatch, test_user, fake_queue):
    payment = create_payment_for_user(db, test_user)

    # Use shared fake_queue at module-level
    monkeypatch.setattr(app_mod, "task_queue", fake_queue, raising=False)

    # Call helper outside of app context; it should attempt to use the transient queue
    module_send_payment_receipt(test_user.id, payment.id)

    # Even though logging may fail due to missing app context, enqueue should have been called
    from tests.helpers import assert_queued

    assert_queued(fake_queue)


def test_send_payment_receipt_job_calls_util_send(app, test_user):
    payment = create_payment_for_user(db, test_user)

    with app.test_request_context():
        with patch("app.utils.email.send_payment_receipt") as mock_send:
            send_payment_receipt_job(test_user.id, payment.id)
            mock_send.assert_called_once()


def test_send_password_reset_job_sends_email(app, test_user, fake_mailer):
    # Ensure test_user has email
    test_user.email = "test@example.com"
    db.session.commit()

    with app.test_request_context():
        # Use shared fake mailer injected into modules used by the job
        inject_fake_mailer(fake_mailer)
        with patch("app.services.background_jobs.render_template") as mock_render:
            mock_render.side_effect = lambda template, **kwargs: f"rendered {template}"
            send_password_reset_job(test_user.id, "token123")
            from tests.helpers import assert_email_sent

            assert_email_sent(fake_mailer, subject_contains="Reset Your Password", recipients=[test_user.email])
