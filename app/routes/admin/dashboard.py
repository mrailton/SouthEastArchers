"""Admin dashboard routes"""
from flask import render_template
from . import bp, admin_required
from app.models import User, Membership, Shoot


@bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    total_members = User.query.count()
    active_memberships = Membership.query.filter_by(status='active').count()
    total_shoots = Shoot.query.count()
    
    recent_members = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        total_members=total_members,
        active_memberships=active_memberships,
        total_shoots=total_shoots,
        recent_members=recent_members
    )
