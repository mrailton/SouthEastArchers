from functools import wraps
from flask import session, redirect, url_for, flash
from app import db


def login_required(f):
    """Login required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Admin required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.models import User
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))

        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('public.index'))

        return f(*args, **kwargs)
    return decorated_function
