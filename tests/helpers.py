"""Test helpers and lightweight fakes used across tests."""

from typing import Any, Callable, List, Tuple


class FakeQueue:
    """Lightweight fake queue that records enqueued jobs.

    It mirrors a minimal interface used in the app: enqueue(callable, *args, **kwargs)
    and stores calls in .enqueued as tuples of (func, args, kwargs).
    """

    def __init__(self) -> None:
        self.enqueued: List[Tuple[Callable[..., Any], tuple, dict]] = []

    def enqueue(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.enqueued.append((func, args, kwargs))


# Small helper to assert an enqueued call contains ids
def last_enqueue_ids(fake_queue: FakeQueue) -> tuple:
    if not fake_queue.enqueued:
        return ()
    _, args, _ = fake_queue.enqueued[-1]
    return args


class FakeMailer:
    """Simple fake mailer that records sent messages instead of performing network IO.

    Designed to replace `app.mail` in tests by assignment: `app.mail = fake_mailer`.
    It collects Message-like objects passed to `send` in `sent_messages`.
    """

    def __init__(self) -> None:
        self.sent_messages: List[Any] = []

    def send(self, message: Any) -> None:
        # Record the message object for assertions in tests
        self.sent_messages.append(message)

    def last_message(self) -> Any:
        return self.sent_messages[-1] if self.sent_messages else None


# Higher-level helpers to reduce duplication in tests
def create_payment_for_user(db, user, **kwargs):
    """Create and persist a Payment for `user` with sensible defaults.

    Accepts override kwargs for fields such as id, amount, amount_cents, payment_method, status, etc.
    Returns the created Payment instance.
    """
    from app.models import Payment

    defaults = {
        "user_id": user.id,
        "amount_cents": kwargs.get("amount_cents", 10000),
        "amount": kwargs.get("amount", kwargs.get("amount_cents", 10000) / 100.0),
        "currency": kwargs.get("currency", "EUR"),
        "payment_type": kwargs.get("payment_type", "membership"),
        "payment_method": kwargs.get("payment_method", "online"),
        "status": kwargs.get("status", "completed"),
        "description": kwargs.get("description", None),
    }

    # Allow passing id and created_at explicitly via kwargs
    all_fields = {**defaults, **{k: v for k, v in kwargs.items() if k in ("id", "created_at", "external_transaction_id", "payment_processor")}}

    payment = Payment(**all_fields)
    db.session.add(payment)
    db.session.commit()
    return payment


def inject_fake_mailer(fake_mailer):
    """Inject `fake_mailer` into commonly-used mail locations so tests don't need to patch.

    This sets the mail object on `app.utils.email` and `app.services.background_jobs` so both
    synchronous helpers and background jobs use the fake when run in tests.
    """
    import app.services.background_jobs as background_jobs
    import app.utils.email as email_mod

    email_mod.mail = fake_mailer
    background_jobs.mail = fake_mailer


def assert_email_sent(fake_mailer, subject_contains=None, recipients=None, html_contains=None, body_contains=None):
    """Assert that at least one email was sent and optionally check its contents.

    Raises AssertionError with helpful message on failure.
    Returns the last message for further assertions.
    """
    if not fake_mailer.sent_messages:
        raise AssertionError("No messages were sent via fake_mailer")

    msg = fake_mailer.last_message()
    if subject_contains and subject_contains not in (msg.subject or ""):
        raise AssertionError(f"Expected subject to contain '{subject_contains}', got '{msg.subject}'")
    if recipients:
        missing = [r for r in recipients if r not in (msg.recipients or [])]
        if missing:
            raise AssertionError(f"Expected recipients {recipients}, missing {missing}")
    if html_contains and html_contains not in (msg.html or ""):
        raise AssertionError(f"Expected html to contain '{html_contains}'")
    if body_contains and body_contains not in (msg.body or ""):
        raise AssertionError(f"Expected body to contain '{body_contains}'")

    return msg


def create_user_with_membership(db, name="Test User", email="test@example.com", credits=20, **kwargs):
    """Create a user with an active membership and return the user.

    Additional user fields can be passed via kwargs.
    """
    from app.models import Membership, User

    user = User(name=name, email=email, phone=kwargs.get("phone", "1234567890"), is_active=kwargs.get("is_active", True))
    user.set_password(kwargs.get("password", "password123"))
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=kwargs.get("start_date"),
        expiry_date=kwargs.get("expiry_date"),
        credits=credits,
        status=kwargs.get("status", "active"),
    )
    # If specific dates not provided, set reasonable defaults
    if membership.start_date is None:
        from datetime import date, timedelta

        membership.start_date = date.today() - timedelta(days=30)
    if membership.expiry_date is None:
        from datetime import date, timedelta

        membership.expiry_date = date.today() + timedelta(days=335)

    db.session.add(membership)
    db.session.commit()
    return user


def assert_queued(fake_queue, expected_func=None, expected_args: tuple | None = None):
    """Assert that a job was enqueued on `fake_queue` and optionally check function and args.

    - expected_func can be a callable or a substring of the repr of the callable.
    - expected_args is a tuple of expected positional args to match the last enqueued job's args.
    """
    if not fake_queue.enqueued:
        raise AssertionError("No jobs were enqueued on fake_queue")

    func, args, kwargs = fake_queue.enqueued[-1]
    if expected_func is not None:
        if callable(expected_func):
            if func is not expected_func:
                raise AssertionError(f"Expected enqueued function {expected_func}, got {func}")
        else:
            if expected_func not in repr(func):
                raise AssertionError(f"Expected enqueued function name to contain '{expected_func}', got {repr(func)}")

    if expected_args is not None:
        if not args:
            raise AssertionError(f"Expected args {expected_args}, but no args were enqueued")
        if args[: len(expected_args)] != expected_args:
            raise AssertionError(f"Expected args starting with {expected_args}, got {args}")

    return func, args, kwargs


def assert_no_email_sent(fake_mailer):
    """Assert no email was sent via the provided fake_mailer.

    Raises AssertionError if any messages were recorded.
    """
    if fake_mailer.sent_messages:
        raise AssertionError(f"Expected no emails to be sent, but found {len(fake_mailer.sent_messages)} messages")


def assert_email_contains(fake_mailer, substring: str):
    """Assert that the last email's html or body contains `substring`.

    Uses assert_email_sent to ensure a message exists and provides a clearer assertion.
    """
    msg = assert_email_sent(fake_mailer)
    if substring not in (msg.html or "") and substring not in (msg.body or ""):
        raise AssertionError(f"Expected email to contain '{substring}'")
