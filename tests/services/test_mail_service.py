from unittest.mock import patch

from app import db
from app.models import Payment, User
from app.services.mail_service import MailService
from app.services.mail_service import send_payment_receipt as module_send_payment_receipt
from tests.helpers import create_payment_for_user, inject_fake_mailer


def test_mailservice_uses_queue_when_available(app, test_user, fake_queue):
    payment = create_payment_for_user(db, test_user)

    with app.test_request_context():
        mail_service = MailService(queue=fake_queue)

        mail_service.send_payment_receipt(test_user.id, payment.id)

        from tests.helpers import assert_queued

        func, args, kwargs = assert_queued(fake_queue)
        assert args[0] == test_user.id
        assert args[1] == payment.id


def test_mailservice_enqueue_raises_falls_back_to_sync(app, test_user):
    payment = create_payment_for_user(db, test_user)

    with app.test_request_context():

        class BadQueue:
            def enqueue(self, *a, **k):
                raise Exception("Queue failure")

        mail_service = MailService(queue=BadQueue())

        with patch("app.utils.email.send_payment_receipt") as mock_send:
            mail_service.send_payment_receipt(test_user.id, payment.id)

            # Should have fallen back to synchronous send
            mock_send.assert_called_once()


def test_mailservice_explicit_none_override_forces_sync(app, test_user, fake_queue):
    payment = create_payment_for_user(db, test_user)

    with app.test_request_context():
        mail_service = MailService(queue=fake_queue)

        with patch("app.utils.email.send_payment_receipt") as mock_send:
            # Explicitly pass None to force synchronous send
            mail_service.send_payment_receipt(test_user.id, payment.id, task_queue_override=None)

            assert len(fake_queue.enqueued) == 0
            mock_send.assert_called_once()


def test_module_helper_prefers_app_registered_instance(app, test_user, fake_queue):
    payment = create_payment_for_user(db, test_user)

    with app.test_request_context():
        # Register an instance on the app
        app.extensions = getattr(app, "extensions", {})
        app.extensions["mail_service"] = MailService(queue=fake_queue)

        module_send_payment_receipt(test_user.id, payment.id)

        from tests.helpers import assert_queued

        func, args, kwargs = assert_queued(fake_queue)
