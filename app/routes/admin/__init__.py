"""Admin routes package"""
from flask import Blueprint, session, redirect, url_for, flash
from functools import wraps
from app import db
from app.models import User

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Admin required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('public.index'))
        
        return f(*args, **kwargs)
    return decorated_function


# Import all route modules to register them with the blueprint
from . import dashboard, members, shoots, news, events
