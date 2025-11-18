#!/usr/bin/env python
"""Management script for South East Archers"""

import click
import os
import sys
from datetime import date, timedelta, datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@click.group()
def cli():
    """South East Archers management commands"""
    pass


# ==============================================================================
# SERVER COMMANDS
# ==============================================================================

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug/--no-debug', default=True, help='Enable debug mode')
def runserver(host, port, debug):
    """Run the Flask development server"""
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1' if debug else '0')
    
    from app import create_app
    app = create_app()
    
    click.echo(f'Starting development server on http://{host}:{port}')
    click.echo(f'Debug mode: {"ON" if debug else "OFF"}')
    app.run(host=host, port=port, debug=debug)


@cli.command()
def shell():
    """Open an interactive Python shell with app context"""
    from app import create_app, db
    from app.models import User, Membership, Shoot, News, Event
    
    app = create_app()
    with app.app_context():
        click.echo('Python shell with app context loaded')
        click.echo('Available: app, db, User, Membership, Shoot, News, Event')
        
        try:
            import IPython
            IPython.embed()
        except ImportError:
            import code
            code.interact(local=dict(
                app=app,
                db=db,
                User=User,
                Membership=Membership,
                Shoot=Shoot,
                News=News,
                Event=Event
            ))


# ==============================================================================
# DATABASE COMMANDS
# ==============================================================================

@cli.group()
def db():
    """Database commands"""
    pass


@db.command()
def init():
    """Initialize database migrations"""
    click.echo('Initializing migrations...')
    os.system('flask db init')


@db.command()
@click.option('-m', '--message', required=True, help='Migration message')
def migrate(message):
    """Create a new migration"""
    click.echo(f'Creating migration: {message}')
    os.system(f'flask db migrate -m "{message}"')


@db.command()
def upgrade():
    """Apply database migrations"""
    click.echo('Applying migrations...')
    os.system('flask db upgrade')


@db.command()
def downgrade():
    """Rollback last migration"""
    if click.confirm('Are you sure you want to rollback the last migration?'):
        click.echo('Rolling back...')
        os.system('flask db downgrade')


@db.command()
def reset():
    """Reset database (WARNING: Deletes all data)"""
    if click.confirm('WARNING: This will delete all data. Continue?'):
        from app import create_app, db as database
        app = create_app()
        with app.app_context():
            click.echo('Dropping all tables...')
            database.drop_all()
            click.echo('Creating all tables...')
            database.create_all()
            click.echo('Database reset complete!')


# ==============================================================================
# USER COMMANDS
# ==============================================================================

@cli.group()
def user():
    """User management commands"""
    pass


@user.command('create')
@click.option('--name', prompt='Full name', help='User full name')
@click.option('--email', prompt='Email', help='User email')
@click.option('--password', prompt=True, hide_input=True, 
              confirmation_prompt=True, help='User password')
@click.option('--phone', default='', help='Phone number (optional)')
@click.option('--dob', prompt='Date of birth (YYYY-MM-DD)', help='Date of birth')
@click.option('--admin', is_flag=True, help='Create as admin user')
@click.option('--with-membership', is_flag=True, default=True, 
              help='Create with membership (default: yes)')
def user_create(name, email, password, phone, dob, admin, with_membership):
    """Create a new user"""
    from app import create_app, db
    from app.models import User, Membership
    
    app = create_app()
    with app.app_context():
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
        
        # Create membership
        if with_membership:
            membership = Membership(
                user_id=user.id,
                start_date=date.today(),
                expiry_date=date.today() + timedelta(days=365),
                status='active'
            )
            db.session.add(membership)
        
        db.session.commit()
        
        user_type = 'admin' if admin else 'member'
        membership_info = ' with membership' if with_membership else ''
        click.echo(f'✓ Successfully created {user_type} user{membership_info}: {email}')


@user.command('list')
def user_list():
    """List all users"""
    from app import create_app, db
    from app.models import User
    
    app = create_app()
    with app.app_context():
        users = User.query.all()
        
        if not users:
            click.echo('No users found')
            return
        
        click.echo('\n{:<5} {:<30} {:<25} {:<10} {:<12}'.format(
            'ID', 'Email', 'Name', 'Admin', 'Membership'))
        click.echo('-' * 90)
        
        for user in users:
            admin_status = 'Yes' if user.is_admin else 'No'
            membership = user.membership
            membership_status = membership.status if membership else 'None'
            click.echo('{:<5} {:<30} {:<25} {:<10} {:<12}'.format(
                user.id, user.email, user.name[:24], admin_status, membership_status))


@user.command('delete')
@click.option('--id', 'user_id', prompt='User ID', type=int, help='User ID to delete')
def user_delete(user_id):
    """Delete a user"""
    from app import create_app, db
    from app.models import User
    
    app = create_app()
    with app.app_context():
        user = User.query.get(user_id)
        
        if not user:
            click.echo(f'Error: User with ID {user_id} not found')
            return
        
        if click.confirm(f'Are you sure you want to delete {user.email}?'):
            db.session.delete(user)
            db.session.commit()
            click.echo(f'✓ User {user.email} deleted successfully')
        else:
            click.echo('Cancelled')


@user.command('admin')
@click.option('--name', prompt='Full name', help='Admin full name')
@click.option('--email', prompt='Email', help='Admin email')
@click.option('--password', prompt=True, hide_input=True, 
              confirmation_prompt=True, help='Admin password')
@click.option('--phone', default='', help='Phone number (optional)')
@click.option('--dob', prompt='Date of birth (YYYY-MM-DD)', 
              default=str(date.today() - timedelta(days=365*30)), help='Date of birth')
def create_admin(name, email, password, phone, dob):
    """Create an admin user with membership (shortcut)"""
    from app import create_app, db
    from app.models import User, Membership
    
    app = create_app()
    with app.app_context():
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
            is_admin=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        # Always create membership for admin
        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status='active'
        )
        db.session.add(membership)
        
        db.session.commit()
        
        click.echo(f'✓ Successfully created admin user with membership: {email}')


# ==============================================================================
# TEST COMMANDS
# ==============================================================================

@cli.group()
def test():
    """Testing commands"""
    pass


@test.command('run')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-c', '--coverage', is_flag=True, help='Run with coverage report')
@click.option('-k', '--keyword', help='Run tests matching keyword')
def test_run(verbose, coverage, keyword):
    """Run test suite"""
    cmd = 'pytest'
    
    if verbose:
        cmd += ' -v'
    
    if coverage:
        cmd += ' --cov=app --cov-report=term-missing --no-cov-on-fail'
    
    if keyword:
        cmd += f' -k "{keyword}"'
    
    click.echo(f'Running: {cmd}')
    exit_code = os.system(cmd)
    sys.exit(exit_code >> 8)


@test.command('file')
@click.argument('filepath')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def test_file(filepath, verbose):
    """Run specific test file"""
    cmd = f'pytest {filepath}'
    if verbose:
        cmd += ' -v'
    
    click.echo(f'Running: {cmd}')
    exit_code = os.system(cmd)
    sys.exit(exit_code >> 8)


@test.command('coverage')
def test_coverage():
    """Run tests with coverage report"""
    click.echo('Running tests with coverage...')
    os.system('pytest --cov=app --cov-report=term-missing --cov-report=html')
    click.echo('\nHTML coverage report generated in htmlcov/')


# ==============================================================================
# CODE QUALITY COMMANDS
# ==============================================================================

@cli.group()
def lint():
    """Code quality commands"""
    pass


@lint.command('check')
def lint_check():
    """Run linting checks"""
    click.echo('Running flake8...')
    exit_code = os.system('flake8 app/ tests/')
    if exit_code == 0:
        click.echo('✓ Linting passed!')
    sys.exit(exit_code >> 8)


@lint.command('format')
@click.option('--check', is_flag=True, help='Check only, do not modify files')
def lint_format(check):
    """Format code with black and isort"""
    if check:
        click.echo('Checking code format...')
        exit_code = os.system('black --check app/ tests/ && isort --check app/ tests/')
    else:
        click.echo('Formatting code...')
        os.system('black app/ tests/')
        os.system('isort app/ tests/')
        click.echo('✓ Code formatted!')
        exit_code = 0
    
    sys.exit(exit_code >> 8)


# ==============================================================================
# SHOOT COMMANDS
# ==============================================================================

@cli.group()
def shoot():
    """Shoot management commands"""
    pass


@shoot.command('create')
@click.option('--location', prompt='Location', help='Shooting location')
@click.option('--date', prompt='Date (YYYY-MM-DD HH:MM)', help='Date and time')
@click.option('--capacity', prompt='Capacity', type=int, default=30, help='Capacity')
@click.option('--description', default='', help='Description (optional)')
def shoot_create(location, date, capacity, description):
    """Create a shoot"""
    from app import create_app, db
    from app.models import Shoot
    
    app = create_app()
    with app.app_context():
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M')
        except ValueError:
            click.echo('Error: Invalid date format. Use YYYY-MM-DD HH:MM')
            return
        
        shoot_obj = Shoot(
            date=date_obj,
            location=location,
            capacity=capacity,
            description=description if description else None
        )
        
        db.session.add(shoot_obj)
        db.session.commit()
        
        click.echo(f'✓ Shoot created: {location} on {date}')


@shoot.command('list')
@click.option('--upcoming', is_flag=True, help='Show only upcoming shoots')
def shoot_list(upcoming):
    """List shoots"""
    from app import create_app, db
    from app.models import Shoot
    
    app = create_app()
    with app.app_context():
        query = Shoot.query
        
        if upcoming:
            query = query.filter(Shoot.date > datetime.now())
        
        shoots = query.order_by(Shoot.date.desc()).all()
        
        if not shoots:
            click.echo('No shoots found')
            return
        
        click.echo('\n{:<5} {:<20} {:<20} {:<10} {:<10}'.format(
            'ID', 'Date', 'Location', 'Capacity', 'Bookings'))
        click.echo('-' * 70)
        
        for s in shoots:
            date_str = s.date.strftime('%Y-%m-%d %H:%M')
            bookings = len(s.bookings) if hasattr(s, 'bookings') else 0
            click.echo('{:<5} {:<20} {:<20} {:<10} {:<10}'.format(
                s.id, date_str, s.location, s.capacity, bookings))


# ==============================================================================
# STATS COMMANDS
# ==============================================================================

@cli.command()
def stats():
    """Show application statistics"""
    from app import create_app, db
    from app.models import User, Membership, Shoot, News, Event
    
    app = create_app()
    with app.app_context():
        total_users = User.query.count()
        total_members = User.query.filter_by(is_admin=False).count()
        total_admins = User.query.filter_by(is_admin=True).count()
        active_memberships = Membership.query.filter_by(status='active').count()
        upcoming_shoots = Shoot.query.filter(
            Shoot.date > datetime.now()
        ).count()
        total_news = News.query.count()
        upcoming_events = Event.query.filter(
            Event.start_date > datetime.now()
        ).count()
        
        click.echo('\n╔══════════════════════════════════════════╗')
        click.echo('║  South East Archers Statistics          ║')
        click.echo('╠══════════════════════════════════════════╣')
        click.echo(f'║  Total users:           {total_users:>15} ║')
        click.echo(f'║  Members:               {total_members:>15} ║')
        click.echo(f'║  Admins:                {total_admins:>15} ║')
        click.echo(f'║  Active memberships:    {active_memberships:>15} ║')
        click.echo(f'║  Upcoming shoots:       {upcoming_shoots:>15} ║')
        click.echo(f'║  Upcoming events:       {upcoming_events:>15} ║')
        click.echo(f'║  News articles:         {total_news:>15} ║')
        click.echo('╚══════════════════════════════════════════╝\n')


# ==============================================================================
# UTILITY COMMANDS
# ==============================================================================

@cli.command()
def clean():
    """Clean cache and temporary files"""
    import shutil
    
    patterns = [
        ('__pycache__', 'directories'),
        ('*.pyc', 'files'),
        ('.pytest_cache', 'directory'),
        ('.coverage', 'file'),
        ('htmlcov', 'directory'),
    ]
    
    click.echo('Cleaning up...')
    
    # Remove __pycache__ directories
    for root, dirs, files in os.walk('.'):
        for d in dirs:
            if d == '__pycache__':
                path = os.path.join(root, d)
                shutil.rmtree(path)
                click.echo(f'  Removed: {path}')
        
        for f in files:
            if f.endswith('.pyc'):
                path = os.path.join(root, f)
                os.remove(path)
                click.echo(f'  Removed: {path}')
    
    # Remove specific directories/files
    if os.path.exists('.pytest_cache'):
        shutil.rmtree('.pytest_cache')
        click.echo('  Removed: .pytest_cache')
    
    if os.path.exists('.coverage'):
        os.remove('.coverage')
        click.echo('  Removed: .coverage')
    
    if os.path.exists('htmlcov'):
        shutil.rmtree('htmlcov')
        click.echo('  Removed: htmlcov')
    
    click.echo('✓ Cleanup complete!')


@cli.command()
def install():
    """Install dependencies with UV"""
    click.echo('Installing dependencies with UV...')
    
    if os.system('which uv > /dev/null 2>&1') != 0:
        click.echo('UV not found. Installing UV...')
        os.system('pip install uv')
    
    os.system('uv sync --group dev')
    click.echo('✓ Dependencies installed!')


if __name__ == '__main__':
    cli()
