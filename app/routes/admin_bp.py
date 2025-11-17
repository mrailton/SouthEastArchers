from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from app import db
from app.utils.datetime_utils import utc_now
from app.models import User, Membership, Shoot, News, Event, Payment
from datetime import datetime, date, timedelta

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
    total_members = User.query.count()
    active_memberships = Membership.query.filter_by(status='active').count()
    upcoming_nights = Shoot.query.filter(
        Shoot.date >= utc_now()
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
    members = User.query.all()
    return render_template('admin/members.html', members=members)


@bp.route('/members/<int:user_id>')
@admin_required
def member_detail(user_id):
    """View member details"""
    member = db.session.get(User, user_id)
    if not member:
        from flask import abort
        abort(404)
    return render_template('admin/member_detail.html', member=member)


@bp.route('/members/<int:user_id>/membership/renew', methods=['POST'])
@admin_required
def renew_membership(user_id):
    """Renew a member's membership"""
    member = db.session.get(User, user_id)
    if not member:
        from flask import abort
        abort(404)
    member.membership.renew()
    db.session.commit()
    
    flash(f'Membership renewed for {member.name}.', 'success')
    return redirect(url_for('admin.member_detail', user_id=user_id))


@bp.route('/shoots')
@admin_required
def shoots():
    """Manage shoots"""
    shoots = Shoot.query.order_by(Shoot.date.desc()).all()
    return render_template('admin/shoots.html', shoots=shoots)


@bp.route('/shoots/create', methods=['GET', 'POST'])
@admin_required
def create_shoot():
    """Create a new shoot and record attendance"""
    from app.forms.admin_forms import ShootForm
    form = ShootForm()
    
    # Populate attendees choices with active members
    active_members = User.query.filter_by(is_active=True).order_by(User.name).all()
    form.attendees.choices = [(u.id, f"{u.name} ({u.membership.credits_remaining()} credits)") 
                               for u in active_members if u.membership and u.membership.is_active()]
    
    if form.validate_on_submit():
        shoot = Shoot(
            date=form.date.data,
            location=form.location.data,
            description=form.description.data
        )
        db.session.add(shoot)
        db.session.flush()
        
        # Add attendees and deduct credits
        attendee_ids = form.attendees.data
        for user_id in attendee_ids:
            user = db.session.get(User, user_id)
            if user and user.membership:
                if user.membership.use_credit():
                    shoot.users.append(user)
                else:
                    flash(f'Warning: {user.name} has no credits remaining.', 'warning')
        
        db.session.commit()
        flash(f'Shoot created with {len(attendee_ids)} attendees!', 'success')
        return redirect(url_for('admin.shoots'))
    
    return render_template('admin/create_shoot.html', form=form)


@bp.route('/shoots/<int:shoot_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_shoot(shoot_id):
    """Edit an existing shoot"""
    from app.forms.admin_forms import ShootForm
    shoot = db.session.get(Shoot, shoot_id)
    if not shoot:
        from flask import abort
        abort(404)
    
    form = ShootForm()
    
    # Populate attendees choices with active members
    active_members = User.query.filter_by(is_active=True).order_by(User.name).all()
    form.attendees.choices = [(u.id, f"{u.name} ({u.membership.credits_remaining()} credits)") 
                               for u in active_members if u.membership and u.membership.is_active()]
    
    if form.validate_on_submit():
        # Track credit changes
        old_attendee_ids = {u.id for u in shoot.users}
        new_attendee_ids = set(form.attendees.data)
        
        # Users removed - refund credits
        removed_ids = old_attendee_ids - new_attendee_ids
        for user_id in removed_ids:
            user = db.session.get(User, user_id)
            if user and user.membership:
                user.membership.add_credits(1)
        
        # Users added - deduct credits
        added_ids = new_attendee_ids - old_attendee_ids
        for user_id in added_ids:
            user = db.session.get(User, user_id)
            if user and user.membership:
                if user.membership.use_credit():
                    shoot.users.append(user)
                else:
                    flash(f'Warning: {user.name} has no credits remaining.', 'warning')
        
        # Remove old attendees
        shoot.users = [u for u in shoot.users if u.id in new_attendee_ids]
        
        # Update shoot details
        shoot.date = form.date.data
        shoot.location = form.location.data
        shoot.description = form.description.data
        
        db.session.commit()
        flash('Shoot updated successfully!', 'success')
        return redirect(url_for('admin.shoots'))
    
    # Pre-populate form
    if request.method == 'GET':
        form.date.data = shoot.date
        form.location.data = shoot.location.name
        form.description.data = shoot.description
        form.attendees.data = [u.id for u in shoot.users]
    
    return render_template('admin/edit_shoot.html', form=form, shoot=shoot)



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


@bp.route('/members/create', methods=['GET', 'POST'])
@admin_required
def create_member():
    """Create a new member"""
    if request.method == 'POST':
        try:
            dob_str = request.form.get('date_of_birth')
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except (ValueError, AttributeError):
            flash('Invalid date format.', 'error')
            return render_template('admin/create_member.html')
        
        # Check if email already exists
        existing = User.query.filter_by(email=request.form.get('email')).first()
        if existing:
            flash('Email already registered.', 'error')
            return render_template('admin/create_member.html')
        
        user = User(
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            date_of_birth=dob,
            is_admin=request.form.get('is_admin') == 'on'
        )
        user.set_password(request.form.get('password', 'changeme123'))
        
        db.session.add(user)
        db.session.flush()
        
        # Create membership if requested
        if request.form.get('create_membership') == 'on':
            membership = Membership(
                user_id=user.id,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=365),
                credits=20,
                status='active'
            )
            db.session.add(membership)
        
        db.session.commit()
        flash(f'Member {user.name} created successfully!', 'success')
        return redirect(url_for('admin.members'))
    
    return render_template('admin/create_member.html')


@bp.route('/members/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_member(user_id):
    """Edit a member"""
    member = db.session.get(User, user_id)
    if not member:
        from flask import abort
        abort(404)
    
    if request.method == 'POST':
        try:
            dob_str = request.form.get('date_of_birth')
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except (ValueError, AttributeError):
            flash('Invalid date format.', 'error')
            return render_template('admin/edit_member.html', member=member)
        
        member.name = request.form.get('name')
        member.email = request.form.get('email')
        member.phone = request.form.get('phone')
        member.date_of_birth = dob
        member.is_admin = request.form.get('is_admin') == 'on'
        member.is_active = request.form.get('is_active') == 'on'
        
        # Update password if provided
        new_password = request.form.get('password')
        if new_password:
            member.set_password(new_password)
        
        # Update membership if exists
        if member.membership:
            try:
                start_date_str = request.form.get('membership_start_date')
                expiry_date_str = request.form.get('membership_expiry_date')
                credits = request.form.get('membership_credits')
                
                if start_date_str:
                    member.membership.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                if expiry_date_str:
                    member.membership.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                if credits:
                    member.membership.credits = int(credits)
            except (ValueError, AttributeError) as e:
                flash(f'Error updating membership: {str(e)}', 'error')
        
        db.session.commit()
        flash(f'Member {member.name} updated successfully!', 'success')
        return redirect(url_for('admin.member_detail', user_id=user_id))
    
    return render_template('admin/edit_member.html', member=member)


@bp.route('/news/<int:news_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_news(news_id):
    """Edit a news article"""
    news = db.session.get(News, news_id)
    if not news:
        from flask import abort
        abort(404)
    
    if request.method == 'POST':
        news.title = request.form.get('title')
        news.summary = request.form.get('summary')
        news.content = request.form.get('content')
        news.published = request.form.get('published') == 'on'
        
        if news.published and not news.published_at:
            news.published_at = utc_now()
        
        db.session.commit()
        flash('News article updated successfully!', 'success')
        return redirect(url_for('admin.news'))
    
    return render_template('admin/edit_news.html', news=news)


@bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    """Edit an event"""
    event = db.session.get(Event, event_id)
    if not event:
        from flask import abort
        abort(404)
    
    if request.method == 'POST':
        try:
            start_date_str = request.form.get('start_date')
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            flash('Invalid date format.', 'error')
            return render_template('admin/edit_event.html', event=event)
        
        event.title = request.form.get('title')
        event.description = request.form.get('description')
        event.start_date = start_date
        event.location = request.form.get('location')
        event.published = request.form.get('published') == 'on'
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/edit_event.html', event=event)
