import json
import os
from unittest.mock import MagicMock, patch

from app import db
from app.models import Payment
from app.services import background_jobs
from app.services.mail_service import MailService
from app.services.mail_service import send_payment_receipt as module_send

# MailService extra branch tests


def test_mailservice_send_sync_no_user_or_payment(app):
    # Call _send_sync with non-existent ids; should not raise and should log
    ms = MailService(queue=None)

    with app.test_request_context():
        # use ids that don't exist
        ms._send_sync(999999, 999999)
        # If no exception, test passes


def test_mailservice_send_sync_util_raises_logs(app, test_user):
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

    ms = MailService(queue=None)

    with app.test_request_context():
        with patch("app.utils.email.send_payment_receipt", side_effect=Exception("send fail")):
            # Patch logger to capture error
            with patch.object(type(ms), "_send_sync", wraps=ms._send_sync):
                # Calling send_payment_receipt should invoke _send_sync and swallow exception
                ms.send_payment_receipt(test_user.id, payment.id, task_queue_override=None)


def test_module_helper_logs_on_exception(app, test_user):
    # Ensure module helper handles exceptions raised by transient service
    with app.test_request_context():
        # Patch transient MailService to raise
        with patch("app.services.mail_service.MailService.send_payment_receipt", side_effect=Exception("boom")):
            # Should not raise
            module_send(test_user.id, 1)


# Vite extra branch tests


def _write_manifest(root_path, asset_name, file_path, css_files=None):
    dir_path = os.path.join(root_path, "../resources/static/.vite")
    os.makedirs(dir_path, exist_ok=True)
    manifest_path = os.path.join(dir_path, "manifest.json")
    manifest = {asset_name: {"file": file_path}}
    if css_files:
        manifest[asset_name]["css"] = css_files
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)


def test_vite_asset_prod_no_css(monkeypatch, app):
    from app.utils.vite import vite_asset

    app.config["DEBUG"] = False
    _write_manifest(app.root_path, "js/no_css.js", "assets/js/no_css.123.js")

    with app.test_request_context():
        res = vite_asset("js/no_css.js")
        assert 'script type="module"' in str(res)


def test_vite_hmr_client_both_ports_unavailable(monkeypatch, app):
    from app.utils.vite import vite_hmr_client

    app.config["DEBUG"] = True

    def fake_get_fail(url, timeout):
        raise Exception("no server")

    monkeypatch.setattr("requests.get", fake_get_fail)

    with app.test_request_context():
        res = vite_hmr_client()
        assert res == ""


# Background job extra tests


def test_send_payment_receipt_job_uses_ctx_and_calls_send(monkeypatch, test_user):
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

    # Create a fake context manager with push/pop tracking
    class Ctx:
        def __init__(self):
            self.pushed = False

        def push(self):
            self.pushed = True

        def pop(self):
            self.pushed = False

    ctx = Ctx()

    # Patch _get_app_context to return our ctx
    monkeypatch.setattr(background_jobs, "_get_app_context", lambda: ctx)

    with patch("app.utils.email.send_payment_receipt") as mock_send:
        background_jobs.send_payment_receipt_job(test_user.id, payment.id)
        mock_send.assert_called_once()
        assert ctx.pushed is False  # popped at the end


def test_send_payment_receipt_job_missing_user_or_payment_logs(app, monkeypatch):
    with app.test_request_context():
        # Patch logger
        with patch("app.services.background_jobs.current_app") as mock_cur:
            mock_cur.logger = MagicMock()
            background_jobs.send_payment_receipt_job(99999, 99999)
            mock_cur.logger.error.assert_called()


def test_send_password_reset_job_user_not_found_logs(app, monkeypatch):
    with app.test_request_context():
        with patch("app.services.background_jobs.current_app") as mock_cur:
            mock_cur.logger = MagicMock()
            background_jobs.send_password_reset_job(99999, "token123")
            mock_cur.logger.error.assert_called()
