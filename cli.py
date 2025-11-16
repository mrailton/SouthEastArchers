#!/usr/bin/env python
"""Management CLI script for South East Archers"""

import click
import os
from datetime import date, timedelta
from app import create_app, db
from app.models import User, Membership, ShootingNight, News, Event
from werkzeug.security import generate_password_hash


def init_app_context(func):
    """Decorator to initialize app context"""
    def wrapper(*args, **kwargs):
        app = create_app(os.environ.get('FLASK_ENV', 'development'))
        with app.app_context():
            return func(*args, **kwargs)
    return wrapper


@click.group()
def cli():
    """South East Archers management CLI"""
    pass


@cli.command()
@init_app_context
def init_db():
    """Initialize the database"""
    click.echo('Creating database tables...')
    db.create_all()
    click.echo('Database initialized successfully!')


@cli.command()
@click.option('--name', prompt='Full name', help='User full name')
@click.option('--email', prompt='Email', help='User email')
@click.option('--password', prompt=True, hide_input=True, 
              confirmation_prompt=True, help='User password')
@click.option('--phone', default='', help='Phone number (optional)')
@click.option('--dob', prompt='Date of birth (YYYY-MM-DD)', help='Date of birth')
@click.option('--admin', is_flag=True, help='Create as admin user')
@init_app_context
def create_user(name, email, password, phone, dob, admin):
    """Create a new user"""
    try:
        dob_obj = date.fromisoformat(dob)
    except ValueError:
        click.echo('Error: Invalid date format. Use YYYY-MM-DD')
        return
    
    if User.query.filter_by(email=email).first():
        click.echo(f'Error: User with email {email} already exists')
        return
    
    user = User(
        name=name,
        email=email,
        phone=phone if phone else None,
        date_of_birth=dob_obj,
        is_admin=admin
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.flush()
    
    # Create membership for non-admin users
    if not admin:
        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status='active'
        )
        db.session.add(membership)
    
    db.session.commit()
    
    user_type = 'admin' if admin else 'member'
    click.echo(f'Successfully created {user_type} user: {email}')


@cli.command()
@init_app_context
def list_users():
    """List all users"""
    users = User.query.all()
    
    if not users:
        click.echo('No users found')
        return
    
    click.echo('\n{:<5} {:<30} {:<20} {:<10}'.format('ID', 'Email', 'Name', 'Admin'))
    click.echo('-' * 70)
    
    for user in users:
        admin_status = 'Yes' if user.is_admin else 'No'
        click.echo('{:<5} {:<30} {:<20} {:<10}'.format(user.id, user.email, user.name, admin_status))


@cli.command()
@click.option('--user-id', prompt='User ID', type=int, help='User ID')
@init_app_context
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get(user_id)
    
    if not user:
        click.echo(f'Error: User with ID {user_id} not found')
        return
    
    if click.confirm(f'Are you sure you want to delete {user.email}?'):
        db.session.delete(user)
        db.session.commit()
        click.echo(f'User {user.email} deleted successfully')
    else:
        click.echo('Cancelled')


@cli.command()
@click.option('--location', prompt='Location', help='Shooting night location')
@click.option('--date', prompt='Date (YYYY-MM-DD HH:MM)', help='Date and time')
@click.option('--capacity', prompt='Capacity', type=int, default=30, help='Capacity')
@click.option('--description', default='', help='Description (optional)')
@init_app_context
def create_shooting_night(location, date, capacity, description):
    """Create a shooting night"""
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M')
    except ValueError:
        click.echo('Error: Invalid date format. Use YYYY-MM-DD HH:MM')
        return
    
    night = ShootingNight(
        date=date_obj,
        location=location,
        capacity=capacity,
        description=description if description else None
    )
    
    db.session.add(night)
    db.session.commit()
    
    click.echo(f'Shooting night created: {location} on {date}')


@cli.command()
@init_app_context
def show_stats():
    """Show statistics"""
    total_users = User.query.count()
    total_members = User.query.filter_by(is_admin=False).count()
    total_admins = User.query.filter_by(is_admin=True).count()
    active_memberships = Membership.query.filter_by(status='active').count()
    upcoming_nights = ShootingNight.query.filter(
        ShootingNight.date > db.func.now()
    ).count()
    
    click.echo('\n=== South East Archers Statistics ===')
    click.echo(f'Total users: {total_users}')
    click.echo(f'Total members: {total_members}')
    click.echo(f'Total admins: {total_admins}')
    click.echo(f'Active memberships: {active_memberships}')
    click.echo(f'Upcoming shooting nights: {upcoming_nights}')


if __name__ == '__main__':
    cli()
