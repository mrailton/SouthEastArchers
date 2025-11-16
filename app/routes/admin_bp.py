from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from app import db
from app.utils.datetime_utils import utc_now
from app.models import User, Membership, ShootingNight, News, Event, Payment
from datetime import datetime

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
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('public.index'))
        
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    total_members = User.query.filter_by(is_admin=False).count()
    active_memberships = Membership.query.filter_by(status='active').count()
    upcoming_nights = ShootingNight.query.filter(
        ShootingNight.date >= utc_now()
    ).count()
    
    return render_template(
        'admin/dashboard.html',
        total_members=total_members,
        active_memberships=active_memberships,
        upcoming_nights=upcoming_nights
    )


@bp.route('/members')
@admin_required
def members():
    """Manage members"""
    members = User.query.filter_by(is_admin=False).all()
    return render_template('admin/members.html', members=members)


@bp.route('/members/<int:user_id>')
@admin_required
def member_detail(user_id):
    """View member details"""
    member = User.query.get_or_404(user_id)
    if member.is_admin:
        flash('Cannot access admin user details.', 'error')
        return redirect(url_for('admin.members'))
    
    return render_template('admin/member_detail.html', member=member)


@bp.route('/members/<int:user_id>/membership/renew', methods=['POST'])
@admin_required
def renew_membership(user_id):
    """Renew a member's membership"""
    member = User.query.get_or_404(user_id)
    member.membership.renew()
    db.session.commit()
    
    flash(f'Membership renewed for {member.name}.', 'success')
    return redirect(url_for('admin.member_detail', user_id=user_id))


@bp.route('/shooting-nights')
@admin_required
def shooting_nights():
    """Manage shooting nights"""
    nights = ShootingNight.query.order_by(ShootingNight.date).all()
    return render_template('admin/shooting_nights.html', nights=nights)


@bp.route('/shooting-nights/create', methods=['GET', 'POST'])
@admin_required
def create_shooting_night():
    """Create a new shooting night"""
    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            flash('Invalid date format.', 'error')
            return render_template('admin/create_shooting_night.html')
        
        night = ShootingNight(
            date=date_obj,
            location=request.form.get('location'),
            description=request.form.get('description'),
            capacity=int(request.form.get('capacity', 30))
        )
        db.session.add(night)
        db.session.commit()
        
        flash('Shooting night created successfully!', 'success')
        return redirect(url_for('admin.shooting_nights'))
    
    return render_template('admin/create_shooting_night.html')


@bp.route('/news')
@admin_required
def news():
    """Manage news"""
    news_items = News.query.order_by(News.created_at.desc()).all()
    return render_template('admin/news.html', news_items=news_items)


@bp.route('/news/create', methods=['GET', 'POST'])
@admin_required
def create_news():
    """Create news"""
    if request.method == 'POST':
        news = News(
            title=request.form.get('title'),
            content=request.form.get('content'),
            summary=request.form.get('summary')
        )
        db.session.add(news)
        db.session.commit()
        
        flash('News created successfully!', 'success')
        return redirect(url_for('admin.news'))
    
    return render_template('admin/create_news.html')


@bp.route('/events')
@admin_required
def events():
    """Manage events"""
    events = Event.query.order_by(Event.start_date).all()
    return render_template('admin/events.html', events=events)


@bp.route('/events/create', methods=['GET', 'POST'])
@admin_required
def create_event():
    """Create event"""
    if request.method == 'POST':
        try:
            start_date = datetime.fromisoformat(
                request.form.get('start_date').replace('Z', '+00:00')
            )
        except (ValueError, AttributeError):
            flash('Invalid date format.', 'error')
            return render_template('admin/create_event.html')
        
        event = Event(
            title=request.form.get('title'),
            description=request.form.get('description'),
            start_date=start_date,
            location=request.form.get('location')
        )
        db.session.add(event)
        db.session.commit()
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/create_event.html')
