from collections.abc import Callable, Sequence
from typing import Any


class FakeQueue:
    """Lightweight fake queue that records enqueued jobs."""

    def __init__(self) -> None:
        self.enqueued: list[tuple[Callable[..., Any], tuple, dict]] = []

    def enqueue(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.enqueued.append((func, args, kwargs))


def last_enqueue_ids(fake_queue: FakeQueue) -> tuple:
    if not fake_queue.enqueued:
        return ()
    _, args, _ = fake_queue.enqueued[-1]
    return args


class SentEmail:
    def __init__(self, subject: str, recipients: Sequence[str], body: str, html: str | None = None) -> None:
        self.subject = subject
        self.recipients = list(recipients)
        self.body = body
        self.html = html


class FakeMailer:
    """Records emails sent via send_email instead of performing network I/O."""

    def __init__(self) -> None:
        self.sent_messages: list[SentEmail] = []

    def record(self, subject: str, recipients: Sequence[str], text_body: str, html_body: str | None = None) -> None:
        self.sent_messages.append(SentEmail(subject, recipients, text_body, html_body))

    def last_message(self) -> SentEmail | None:
        return self.sent_messages[-1] if self.sent_messages else None


_UNSET = object()


class FakePaymentProcessor:
    """Drop-in replacement for SumUpService to avoid real API calls in tests."""

    def __init__(
        self,
        checkout_response: dict[str, Any] | None = _UNSET,
        get_checkout_response: Any = None,
        verify_result: bool = True,
    ) -> None:
        self.checkout_response = {"id": "fake_checkout_id", "status": "PENDING"} if checkout_response is _UNSET else checkout_response
        self.get_checkout_response = get_checkout_response
        self.verify_result = verify_result
        self.calls: list[tuple[str, tuple, dict]] = []

    def create_checkout(self, **kwargs: Any) -> dict[str, Any] | None:
        self.calls.append(("create_checkout", (), kwargs))
        return self.checkout_response

    def get_checkout(self, checkout_id: str) -> Any:
        self.calls.append(("get_checkout", (checkout_id,), {}))
        return self.get_checkout_response

    def verify_payment(self, checkout_id: str) -> bool:
        self.calls.append(("verify_payment", (checkout_id,), {}))
        return self.verify_result


def create_payment_for_user(db, user, **kwargs):
    from app.enums import PaymentMethod, PaymentType
    from app.models import Payment

    defaults = {
        "user_id": user.id,
        "amount_cents": kwargs.get("amount_cents", 10000),
        "amount": kwargs.get("amount", kwargs.get("amount_cents", 10000) / 100.0),
        "currency": kwargs.get("currency", "EUR"),
        "payment_type": kwargs.get("payment_type", PaymentType.MEMBERSHIP),
        "payment_method": kwargs.get("payment_method", PaymentMethod.ONLINE),
        "status": kwargs.get("status", "completed"),
        "description": kwargs.get("description", None),
    }
    all_fields = {
        **defaults,
        **{k: v for k, v in kwargs.items() if k in ("id", "created_at", "external_transaction_id", "payment_processor")},
    }
    payment = Payment(**all_fields)
    db.session.add(payment)
    db.session.commit()
    return payment


def inject_fake_mailer(fake_mailer: FakeMailer) -> None:
    """Patch send_email so tests capture messages without SMTP."""

    def _fake_send(subject: str, recipients: Sequence[str], text_body: str, html_body: str | None = None) -> None:
        fake_mailer.record(subject, recipients, text_body, html_body)

    import app.services.mail_service as mail_service_mod
    import app.utils.mail as mail_mod

    mail_mod.send_email = _fake_send
    mail_service_mod.send_email = _fake_send


def assert_email_sent(fake_mailer, subject_contains=None, recipients=None, html_contains=None, body_contains=None):
    if not fake_mailer.sent_messages:
        raise AssertionError("No messages were sent via fake_mailer")

    msg = fake_mailer.last_message()
    assert msg is not None
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
    from app.models import Membership, User

    user = User(name=name, email=email, phone=kwargs.get("phone", "1234567890"), is_active=kwargs.get("is_active", True))
    user.set_password(kwargs.get("password", "password123"))
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=kwargs.get("start_date"),
        expiry_date=kwargs.get("expiry_date"),
        initial_credits=credits,
        purchased_credits=kwargs.get("purchased_credits", 0),
        status=kwargs.get("status", "active"),
    )
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
    if not fake_queue.enqueued:
        raise AssertionError("No jobs were enqueued on fake_queue")

    func, args, kwargs = fake_queue.enqueued[-1]
    if expected_func is not None:
        if callable(expected_func):
            if func is not expected_func:
                raise AssertionError(f"Expected enqueued function {expected_func}, got {func}")
        elif expected_func not in repr(func):
            raise AssertionError(f"Expected enqueued function name to contain '{expected_func}', got {repr(func)}")

    if expected_args is not None:
        if not args:
            raise AssertionError(f"Expected args {expected_args}, but no args were enqueued")
        if args[: len(expected_args)] != expected_args:
            raise AssertionError(f"Expected args starting with {expected_args}, got {args}")

    return func, args, kwargs


def assert_no_email_sent(fake_mailer):
    if fake_mailer.sent_messages:
        raise AssertionError(f"Expected no emails to be sent, but found {len(fake_mailer.sent_messages)} messages")


def assert_email_contains(fake_mailer, substring: str):
    msg = assert_email_sent(fake_mailer)
    if substring not in (msg.html or "") and substring not in (msg.body or ""):
        raise AssertionError(f"Expected email to contain '{substring}'")


_custom_role_counter = 0


def create_user_with_permissions(db, permissions: list[str], **kwargs):
    global _custom_role_counter

    from app.models import Permission, Role, User

    _custom_role_counter += 1
    name = kwargs.pop("name", f"Custom User {_custom_role_counter}")
    email = kwargs.pop("email", f"custom{_custom_role_counter}@example.com")
    password = kwargs.pop("password", "password123")

    user = User(
        name=name,
        email=email,
        phone=kwargs.pop("phone", "0000000000"),
        is_active=kwargs.pop("is_active", True),
        **kwargs,
    )
    user.set_password(password)

    perm_objects = Permission.query.filter(Permission.name.in_(permissions)).all()
    found_names = {p.name for p in perm_objects}
    missing = set(permissions) - found_names
    if missing:
        raise ValueError(f"Permissions not found (run seed_rbac first): {missing}")

    role = Role(name=f"_test_role_{_custom_role_counter}", description="Auto-generated test role")
    role.permissions = perm_objects
    user.roles.append(role)

    db.session.add(user)
    db.session.commit()
    return user
