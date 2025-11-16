from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import User, Membership
from datetime import date, timedelta
import secrets

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            session.permanent = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('member.dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        dob_str = request.form.get('date_of_birth')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Validation
        if not all([name, email, dob_str, password]):
            flash('All required fields must be filled.', 'error')
            return render_template('auth/signup.html')
        
        if password != password_confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/signup.html')
        
        try:
            dob = date.fromisoformat(dob_str)
        except ValueError:
            flash('Invalid date of birth.', 'error')
            return render_template('auth/signup.html')
        
        # Create user
        user = User(
            name=name,
            email=email,
            phone=phone,
            date_of_birth=dob
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        # Create membership
        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status='active'
        )
        db.session.add(membership)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/signup.html')


@bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('public.index'))


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password request"""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # TODO: Send reset email
            flash('Check your email for password reset instructions.', 'info')
        else:
            flash('If an account exists with that email, you will receive a password reset link.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    # TODO: Implement token verification
    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html')
        
        # TODO: Reset password for user
        flash('Password reset successfully. Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html')
