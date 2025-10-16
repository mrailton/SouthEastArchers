from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.forms import NewsForm, EventForm, ShootingNightForm
from app.models import News, Event, User, ShootingNight

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_members = User.query.count()
    total_news = News.query.count()
    total_events = Event.query.count()
    return render_template('admin/dashboard.html', 
                         total_members=total_members,
                         total_news=total_news,
                         total_events=total_events)

# News Management
@bp.route('/news')
@login_required
@admin_required
def news_list():
    news = News.query.order_by(News.created_at.desc()).all()
    return render_template('admin/news_list.html', news=news)

@bp.route('/news/create', methods=['GET', 'POST'])
@login_required
@admin_required
def news_create():
    form = NewsForm()
    if form.validate_on_submit():
        news = News(
            title=form.title.data,
            content=form.content.data,
            published=form.published.data,
            author_id=current_user.id
        )
        db.session.add(news)
        db.session.commit()
        flash('News article created successfully!', 'success')
        return redirect(url_for('admin.news_list'))
    return render_template('admin/news_form.html', form=form, title='Create News')

@bp.route('/news/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def news_edit(id):
    news = News.query.get_or_404(id)
    form = NewsForm(obj=news)
    
    if form.validate_on_submit():
        news.title = form.title.data
        news.content = form.content.data
        news.published = form.published.data
        db.session.commit()
        flash('News article updated successfully!', 'success')
        return redirect(url_for('admin.news_list'))
    
    return render_template('admin/news_form.html', form=form, title='Edit News')

@bp.route('/news/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def news_delete(id):
    news = News.query.get_or_404(id)
    db.session.delete(news)
    db.session.commit()
    flash('News article deleted successfully!', 'success')
    return redirect(url_for('admin.news_list'))

# Event Management
@bp.route('/events')
@login_required
@admin_required
def event_list():
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('admin/event_list.html', events=events)

@bp.route('/events/create', methods=['GET', 'POST'])
@login_required
@admin_required
def event_create():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            event_date=form.event_date.data,
            location=form.location.data,
            published=form.published.data,
            created_by=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin.event_list'))
    return render_template('admin/event_form.html', form=form, title='Create Event')

@bp.route('/events/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def event_edit(id):
    event = Event.query.get_or_404(id)
    form = EventForm(obj=event)
    
    if form.validate_on_submit():
        event.title = form.title.data
        event.description = form.description.data
        event.event_date = form.event_date.data
        event.location = form.location.data
        event.published = form.published.data
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin.event_list'))
    
    return render_template('admin/event_form.html', form=form, title='Edit Event')

@bp.route('/events/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def event_delete(id):
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin.event_list'))

# Member Management
@bp.route('/members')
@login_required
@admin_required
def member_list():
    members = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/member_list.html', members=members)

@bp.route('/members/<int:id>')
@login_required
@admin_required
def member_detail(id):
    member = User.query.get_or_404(id)
    return render_template('admin/member_detail.html', member=member)

# Shooting Night Management
@bp.route('/shooting-nights')
@login_required
@admin_required
def shooting_night_list():
    shooting_nights = ShootingNight.query.order_by(ShootingNight.date.desc()).all()
    return render_template('admin/shooting_night_list.html', shooting_nights=shooting_nights)

@bp.route('/shooting-nights/create', methods=['GET', 'POST'])
@login_required
@admin_required
def shooting_night_create():
    form = ShootingNightForm()
    # Get all active members with current memberships
    members = User.query.filter_by(is_active=True).order_by(User.name).all()
    form.attendees.choices = [(m.id, m.name) for m in members]
    
    if form.validate_on_submit():
        shooting_night = ShootingNight(
            date=form.date.data,
            location=form.location.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(shooting_night)
        db.session.flush()  # Get the ID before adding attendees
        
        # Add attendees and deduct credits
        for user_id in form.attendees.data:
            user = User.query.get(user_id)
            if user:
                shooting_night.attendees.append(user)
                
                # Deduct one credit from user's current membership
                membership = user.current_membership
                if membership and membership.credits_remaining > 0:
                    membership.credits_remaining -= 1
        
        db.session.commit()
        flash('Shooting night recorded successfully!', 'success')
        return redirect(url_for('admin.shooting_night_list'))
    
    return render_template('admin/shooting_night_form.html', form=form, title='Record Shooting Night')

@bp.route('/shooting-nights/<int:id>')
@login_required
@admin_required
def shooting_night_detail(id):
    shooting_night = ShootingNight.query.get_or_404(id)
    return render_template('admin/shooting_night_detail.html', shooting_night=shooting_night)

@bp.route('/shooting-nights/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def shooting_night_edit(id):
    shooting_night = ShootingNight.query.get_or_404(id)
    form = ShootingNightForm(obj=shooting_night)
    
    # Get all active members
    members = User.query.filter_by(is_admin=False, is_active=True).order_by(User.name).all()
    form.attendees.choices = [(m.id, m.name) for m in members]
    
    if request.method == 'GET':
        # Pre-select current attendees
        form.attendees.data = [attendee.id for attendee in shooting_night.attendees]
    
    if form.validate_on_submit():
        # Get previous attendees
        previous_attendees = set(shooting_night.attendees)
        new_attendees_ids = set(form.attendees.data)
        
        # Find who was added and who was removed
        previous_attendees_ids = {a.id for a in previous_attendees}
        added_ids = new_attendees_ids - previous_attendees_ids
        removed_ids = previous_attendees_ids - new_attendees_ids
        
        # Restore credits for removed attendees
        for user_id in removed_ids:
            user = User.query.get(user_id)
            if user:
                membership = user.current_membership
                if membership:
                    membership.credits_remaining += 1
        
        # Deduct credits for newly added attendees
        for user_id in added_ids:
            user = User.query.get(user_id)
            if user:
                membership = user.current_membership
                if membership and membership.credits_remaining > 0:
                    membership.credits_remaining -= 1
        
        # Update shooting night details
        shooting_night.date = form.date.data
        shooting_night.location = form.location.data
        shooting_night.notes = form.notes.data
        
        # Update attendees
        shooting_night.attendees = [User.query.get(uid) for uid in form.attendees.data]
        
        db.session.commit()
        flash('Shooting night updated successfully!', 'success')
        return redirect(url_for('admin.shooting_night_list'))
    
    return render_template('admin/shooting_night_form.html', form=form, title='Edit Shooting Night', shooting_night=shooting_night)

@bp.route('/shooting-nights/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def shooting_night_delete(id):
    shooting_night = ShootingNight.query.get_or_404(id)
    
    # Restore credits to all attendees
    for attendee in shooting_night.attendees:
        membership = attendee.current_membership
        if membership:
            membership.credits_remaining += 1
    
    db.session.delete(shooting_night)
    db.session.commit()
    flash('Shooting night deleted and credits restored!', 'success')
    return redirect(url_for('admin.shooting_night_list'))
