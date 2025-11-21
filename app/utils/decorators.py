from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Admin required decorator"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))

        if not current_user.is_admin:
            flash("You do not have permission to access this page.", "error")
            abort(403)

        return f(*args, **kwargs)

    return decorated_function
