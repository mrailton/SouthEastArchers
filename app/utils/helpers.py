from collections.abc import Sequence

from app.utils.mail import send_email

__all__ = ["send_email", "parse_visitors_from_form"]

from app.utils.formdata import parse_visitors_from_form  # noqa: E402
