from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from functools import wraps
from app import db
from app.models import User, Payment, Credit, Membership
from app.services import SumUpService
from datetime import date, timedelta
import secrets

bp = Blueprint('payment', __name__, url_prefix='/payment')


def login_required(f):
    """Login required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/membership', methods=['GET', 'POST'])
def membership_payment():
    """Membership payment page"""
    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user = db.session.get(User, session['user_id'])
        amount = current_app.config['ANNUAL_MEMBERSHIP_COST']
        
        # Create payment record
        payment = Payment(
            user_id=user.id,
            amount=amount,
            currency='EUR',
            payment_type='membership',
            description=f'Annual Membership for {user.name}'
        )
        db.session.add(payment)
        db.session.commit()
        
        # Initialize Sum Up checkout
        sumup_service = SumUpService()
        return_url = request.host_url.rstrip('/') + url_for('payment.membership_callback')
        
        checkout = sumup_service.create_checkout(
            amount=amount,
            currency='EUR',
            description='Annual Membership',
            return_url=return_url
        )
        
        if checkout:
            # Redirect to Sum Up checkout
            return redirect(checkout.get('checkout_url'))
        else:
            flash('Error creating payment. Please try again.', 'error')
            db.session.delete(payment)
            db.session.commit()
    
    return render_template('payment/membership.html')


@bp.route('/credits', methods=['GET', 'POST'])
@login_required
def credit_payment():
    """Purchase additional shooting credits"""
    if request.method == 'POST':
        user = db.session.get(User, session['user_id'])
        quantity = int(request.form.get('quantity', 1))
        amount = quantity * current_app.config['ADDITIONAL_NIGHT_COST']
        
        # Create payment record
        payment = Payment(
            user_id=user.id,
            amount=amount,
            currency='EUR',
            payment_type='credits',
            description=f'{quantity} shooting credits'
        )
        db.session.add(payment)
        db.session.commit()
        
        # Initialize Sum Up checkout
        sumup_service = SumUpService()
        return_url = request.host_url.rstrip('/') + url_for('payment.credit_callback')
        
        checkout = sumup_service.create_checkout(
            amount=amount,
            currency='EUR',
            description=f'{quantity} shooting credits',
            return_url=return_url
        )
        
        if checkout:
            return redirect(checkout.get('checkout_url'))
        else:
            flash('Error creating payment. Please try again.', 'error')
            db.session.delete(payment)
            db.session.commit()
    
    return render_template('payment/credits.html')


@bp.route('/membership/callback')
def membership_callback():
    """Sum Up membership payment callback"""
    transaction_id = request.args.get('transaction_id')
    
    if not transaction_id:
        flash('Payment cancelled.', 'warning')
        return redirect(url_for('member.dashboard'))
    
    # Verify payment with Sum Up
    sumup_service = SumUpService()
    if sumup_service.verify_payment(transaction_id):
        # Find pending payment
        payment = Payment.query.filter_by(
            sumup_transaction_id=transaction_id,
            status='pending'
        ).first()
        
        if not payment:
            payment = Payment.query.filter_by(
                user_id=session.get('user_id'),
                payment_type='membership',
                status='pending'
            ).first()
        
        if payment:
            payment.mark_completed(transaction_id)
            
            # Update membership
            user = db.session.get(User, payment.user_id)
            if user.membership:
                user.membership.renew()
            else:
                membership = Membership(
                    user_id=user.id,
                    start_date=date.today(),
                    expiry_date=date.today() + timedelta(days=365),
                    status='active'
                )
                db.session.add(membership)
            
            db.session.commit()
            flash('Membership payment successful!', 'success')
        
        return redirect(url_for('member.dashboard'))
    else:
        flash('Payment verification failed. Please contact support.', 'error')
        return redirect(url_for('payment.membership_payment'))


@bp.route('/credits/callback')
def credit_callback():
    """Sum Up credit payment callback"""
    transaction_id = request.args.get('transaction_id')
    
    if not transaction_id:
        flash('Payment cancelled.', 'warning')
        return redirect(url_for('member.credits'))
    
    # Verify payment with Sum Up
    sumup_service = SumUpService()
    if sumup_service.verify_payment(transaction_id):
        # Find pending payment
        payment = Payment.query.filter_by(
            user_id=session.get('user_id'),
            payment_type='credits',
            status='pending'
        ).first()
        
        if payment:
            payment.mark_completed(transaction_id)
            
            # Create credits for user
            quantity = int(payment.amount / current_app.config['ADDITIONAL_NIGHT_COST'])
            credit = Credit(
                user_id=payment.user_id,
                amount=quantity,
                payment_id=payment.id
            )
            db.session.add(credit)
            db.session.commit()
            
            flash(f'Successfully purchased {quantity} credits!', 'success')
        
        return redirect(url_for('member.credits'))
    else:
        flash('Payment verification failed. Please contact support.', 'error')
        return redirect(url_for('payment.credit_payment'))


@bp.route('/history')
@login_required
def history():
    """View payment history"""
    user = db.session.get(User, session['user_id'])
    payments = Payment.query.filter_by(
        user_id=user.id
    ).order_by(Payment.created_at.desc()).all()
    
    return render_template('payment/history.html', payments=payments)
