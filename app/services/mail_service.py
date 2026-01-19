from flask import current_app

_DEFAULT_TASK_QUEUE_SENTINEL = object()


class MailService:
    def __init__(self, queue=None, mailer=None):
        """Instance MailService that holds injected dependencies.

        - queue: an object exposing an `enqueue(callable, *args)` method (optional)
        - mailer: optional mail client (not required; existing app.utils.email used as fallback)
        """
        self.queue = queue
        self.mailer = mailer

    def send_payment_receipt(self, user_id: int, payment_id: int, task_queue_override=_DEFAULT_TASK_QUEUE_SENTINEL) -> None:
        """Send or queue a payment receipt using the configured queue or a provided override.

        If `task_queue_override` is explicitly passed as None, that forces synchronous send.
        If not passed, the instance's `queue` field is used.
        """
        if task_queue_override is _DEFAULT_TASK_QUEUE_SENTINEL:
            tq = self.queue
        else:
            tq = task_queue_override

        enqueue = getattr(tq, "enqueue", None)
        if callable(enqueue):
            try:
                # local import to avoid circular imports in worker contexts
                from app.services.background_jobs import send_payment_receipt_job

                enqueue(send_payment_receipt_job, user_id, payment_id)
                current_app.logger.info(f"Queued payment receipt email for user {user_id}, payment {payment_id}")
                return
            except Exception as e:
                current_app.logger.error(f"Failed to enqueue receipt email job: {str(e)} -- falling back to sync send")

        # Fallback to synchronous send
        self._send_sync(user_id, payment_id)

    def _send_sync(self, user_id: int, payment_id: int) -> None:
        try:
            # Import on demand to keep module-level imports light and avoid cycles
            from app import db
            from app.models import Payment, User
            from app.utils.email import send_payment_receipt as util_send
        except Exception as e:
            current_app.logger.error(f"Failed to import mail utilities or models: {e}")
            return

        try:
            user = db.session.get(User, user_id)
            payment = db.session.get(Payment, payment_id)

            if not user or not payment:
                current_app.logger.error(f"Cannot send receipt — user or payment not found (user_id={user_id}, payment_id={payment_id})")
                return

            # Delegate formatting/sending to the utility
            util_send(user, payment, user.membership)
            current_app.logger.info(f"Sent payment receipt email for user {user_id}, payment {payment_id}")
        except Exception as e:
            current_app.logger.error(f"Failed to send receipt email synchronously: {e}")


# Backwards-compatible helper function used by existing callers/tests.
def send_payment_receipt(user_id: int, payment_id: int, task_queue_override=_DEFAULT_TASK_QUEUE_SENTINEL) -> None:
    """Module-level helper that prefers an app-registered MailService instance.

    If `current_app` has a registered mail service at `current_app.extensions['mail_service']`,
    that instance will be used (and the `task_queue_override` passed through). Otherwise a
    transient MailService is created using the app-level `task_queue` if available.
    """
    try:
        mail_service = None
        try:
            mail_service = current_app.extensions.get("mail_service")
        except RuntimeError:
            # No app context — fall back to transient
            mail_service = None

        if mail_service is not None:
            # Delegate to the registered instance
            mail_service.send_payment_receipt(user_id, payment_id, task_queue_override=task_queue_override)
            return

        # No registered instance — create a transient one using the app's task_queue if present
        from app import task_queue

        transient = MailService(queue=task_queue)
        transient.send_payment_receipt(user_id, payment_id, task_queue_override=task_queue_override)
    except Exception as e:
        # Defensive logging without raising
        try:
            current_app.logger.error(f"MailService helper failed: {e}")
        except RuntimeError:
            pass
