from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from app import db
from app.utils.datetime_utils import utc_now
from app.models import User, Membership, ShootingNight, Credit, Payment
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
    credits = Credit.query.filter_by(user_id=user.id).all()
    available_credits = sum(c.balance() for c in credits if not c.is_expired())
    
    return render_template(
        'member/dashboard.html',
        user=user,
        membership=membership,
        available_credits=available_credits
    )


@bp.route('/shooting-nights')
@login_required
def shooting_nights():
    """View available shooting nights"""
    user = db.session.get(User, session['user_id'])
    
    # Get upcoming shooting nights
    nights = ShootingNight.query.filter(
        ShootingNight.date >= utc_now()
    ).order_by(ShootingNight.date).all()
    
    # Get user's registered nights
    user_night_ids = [n.id for n in user.shooting_nights]
    
    return render_template(
        'member/shooting_nights.html',
        nights=nights,
        user_night_ids=user_night_ids
    )


@bp.route('/shooting-nights/<int:night_id>/register', methods=['POST'])
@login_required
def register_shooting_night(night_id):
    """Register for a shooting night"""
    user = db.session.get(User, session['user_id'])
    night = db.session.get(ShootingNight, night_id)
    if not night:
        from flask import abort
        abort(404)
    
    # Check if already registered
    if night in user.shooting_nights:
        flash('You are already registered for this night.', 'warning')
        return redirect(url_for('member.shooting_nights'))
    
    # Check capacity
    if night.is_full():
        flash('This shooting night is full.', 'error')
        return redirect(url_for('member.shooting_nights'))
    
    # Check credits/membership
    membership = user.membership
    credits = Credit.query.filter_by(user_id=user.id).all()
    available_credits = sum(c.balance() for c in credits if not c.is_expired())
    
    if membership.nights_remaining() > 0:
        membership.nights_used += 1
    elif available_credits > 0:
        # Use a credit
        for credit in credits:
            if credit.balance() > 0 and not credit.is_expired():
                credit.used += 1
                break
    else:
        flash('No available credits. Please purchase additional credits.', 'error')
        return redirect(url_for('member.shooting_nights'))
    
    user.shooting_nights.append(night)
    db.session.commit()
    
    flash('Successfully registered for this shooting night!', 'success')
    return redirect(url_for('member.shooting_nights'))


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
