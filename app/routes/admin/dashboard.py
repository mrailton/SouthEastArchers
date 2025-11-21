"""Admin dashboard routes"""
from datetime import date, timedelta
from flask import render_template
from . import bp, admin_required
from app.models import User, Membership, Shoot


@bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with key statistics and recent activity"""
    total_members = User.query.count()
    active_memberships = Membership.query.filter_by(status='active').count()
    
    # Count memberships expiring in the next 30 days
    today = date.today()
    expiry_threshold = today + timedelta(days=30)
    expiring_soon = Membership.query.filter(
        Membership.status == 'active',
        Membership.expiry_date <= expiry_threshold,
        Membership.expiry_date >= today
    ).count()
    
    # Get the 5 most recently created members
    recent_members = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        total_members=total_members,
        active_memberships=active_memberships,
        expiring_soon=expiring_soon,
        recent_members=recent_members
    )
