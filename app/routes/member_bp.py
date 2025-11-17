from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from app import db
from app.utils.datetime_utils import utc_now
from app.models import User, Membership, Shoot, Credit, Payment
from datetime import datetime

bp = Blueprint('member', __name__, url_prefix='/member')


def login_required(f):
    """Login required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/dashboard')
@login_required
def dashboard():
    """Member dashboard"""
    user = db.session.get(User, session['user_id'])
    membership = user.membership
    
    # Get shoot count
    shoots_attended = len(user.shoots)
    
    return render_template(
        'member/dashboard.html',
        user=user,
        membership=membership,
        shoots_attended=shoots_attended
    )


@bp.route('/shoots')
@login_required
def shoots():
    """View shoot history"""
    user = db.session.get(User, session['user_id'])
    
    # Get user's shoot history
    user_shoots = Shoot.query.join(Shoot.users).filter(User.id == user.id).order_by(Shoot.date.desc()).all()
    
    return render_template('member/shoots.html', shoots=user_shoots, user=user)


@bp.route('/credits')
@login_required
def credits():
    """View and purchase credits"""
    user = db.session.get(User, session['user_id'])
    credits = Credit.query.filter_by(user_id=user.id).all()
    
    return render_template('member/credits.html', credits=credits, user=user)


@bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = db.session.get(User, session['user_id'])
    return render_template('member/profile.html', user=user)


@bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    user = db.session.get(User, session['user_id'])
    
    user.name = request.form.get('name', user.name)
    user.phone = request.form.get('phone', user.phone)
    
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('member.profile'))


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password"""
    if request.method == 'POST':
        user = db.session.get(User, session['user_id'])
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('member/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('member/change_password.html')
        
        user.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('member.profile'))
    
    return render_template('member/change_password.html')
