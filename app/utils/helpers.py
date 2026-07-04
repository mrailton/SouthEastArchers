from app.utils.mail import send_email

__all__ = ["send_email", "parse_visitors_from_form", "is_safe_redirect"]

from app.utils.formdata import parse_visitors_from_form  # noqa: E402


def is_safe_redirect(url: str) -> bool:
    """Return True only for relative paths that cannot be open redirects.

    ``startswith("/")`` alone allows ``//evil.com`` (protocol-relative).
    This helper also rejects those.
    """
    return bool(url) and url.startswith("/") and not url.startswith("//")
