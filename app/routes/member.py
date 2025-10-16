from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import CreditPurchase, Membership
from app.forms import CreditPurchaseForm
from config import Config

bp = Blueprint('member', __name__, url_prefix='/member')

@bp.route('/dashboard')
@login_required
def dashboard():
    membership = current_user.current_membership
    recent_purchases = CreditPurchase.query.filter_by(user_id=current_user.id).order_by(CreditPurchase.purchase_date.desc()).limit(5).all()
    return render_template('member/dashboard.html', membership=membership, purchases=recent_purchases)

@bp.route('/credits/purchase', methods=['GET', 'POST'])
@login_required
def purchase_credits():
    form = CreditPurchaseForm()
    
    if form.validate_on_submit():
        credits = form.credits.data
        amount = credits * Config.CREDIT_COST
        
        # Create credit purchase record
        purchase = CreditPurchase(
            user_id=current_user.id,
            credits_purchased=credits,
            amount_paid=amount
        )
        
        # Add credits to current membership
        membership = current_user.current_membership
        if membership:
            membership.credits_remaining += credits
        
        db.session.add(purchase)
        db.session.commit()
        
        flash(f'Successfully purchased {credits} credits for €{amount}!', 'success')
        return redirect(url_for('member.dashboard'))
    
    return render_template('member/purchase_credits.html', form=form, credit_cost=Config.CREDIT_COST)

@bp.route('/profile')
@login_required
def profile():
    return render_template('member/profile.html')
