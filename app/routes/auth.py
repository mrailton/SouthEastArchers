from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.models import User, Membership
from app.forms import LoginForm, RegistrationForm
from datetime import datetime, timedelta

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            name=form.name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        
        # Create initial membership
        membership = Membership(
            user=user,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=365),
            credits_remaining=20,
            amount_paid=100.0
        )
        
        db.session.add(user)
        db.session.add(membership)
        db.session.commit()
        
        flash('Registration successful! Your membership includes 20 shooting credits.', 'success')
        login_user(user)
        return redirect(url_for('member.dashboard'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
