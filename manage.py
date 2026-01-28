#!/usr/bin/env python
"""Management script for South East Archers"""

import os
import sys
import warnings
from datetime import date, datetime, timedelta

import click
from dotenv import load_dotenv

# Suppress SyntaxWarning from third-party libraries (e.g., sumup package)
warnings.filterwarnings("ignore", category=SyntaxWarning)

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
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=5000, help="Port to bind to")
@click.option("--debug/--no-debug", default=True, help="Enable debug mode")
def runserver(host, port, debug):
    """Run the Flask development server"""
    os.environ.setdefault("FLASK_ENV", "development")
    os.environ.setdefault("FLASK_DEBUG", "1" if debug else "0")

    from app import create_app

    app = create_app()

    click.echo(f"Starting development server on http://{host}:{port}")
    click.echo(f'Debug mode: {"ON" if debug else "OFF"}')
    app.run(host=host, port=port, debug=debug)


@cli.command()
def shell():
    """Open an interactive Python shell with app context"""
    from app import create_app, db
    from app.models import Event, Membership, News, Shoot, User

    app = create_app()
    with app.app_context():
        click.echo("Python shell with app context loaded")
        click.echo("Available: app, db, User, Membership, Shoot, News, Event")

        try:
            import IPython

            IPython.embed()
        except ImportError:
            import code

            code.interact(
                local=dict(
                    app=app,
                    db=db,
                    User=User,
                    Membership=Membership,
                    Shoot=Shoot,
                    News=News,
                    Event=Event,
                )
            )


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
    click.echo("Initializing migrations...")
    os.system("flask db init")


@db.command()
@click.option("-m", "--message", required=True, help="Migration message")
def migrate(message):
    """Create a new migration"""
    click.echo(f"Creating migration: {message}")
    os.system(f'flask db migrate -m "{message}"')


@db.command()
def upgrade():
    """Apply database migrations"""
    click.echo("Applying migrations...")
    os.system("flask db upgrade")


@db.command()
def downgrade():
    """Rollback last migration"""
    if click.confirm("Are you sure you want to rollback the last migration?"):
        click.echo("Rolling back...")
        os.system("flask db downgrade")


@db.command()
def reset():
    """Reset database (WARNING: Deletes all data)"""
    if click.confirm("WARNING: This will delete all data. Continue?"):
        from app import create_app
        from app import db as database

        app = create_app()
        with app.app_context():
            click.echo("Dropping all tables...")
            database.drop_all()
            click.echo("Creating all tables...")
            database.create_all()
            click.echo("Database reset complete!")


# ==============================================================================
# USER COMMANDS
# ==============================================================================


@cli.group()
def user():
    """User management commands"""
    pass


@user.command("create")
@click.option("--name", prompt="Full name", help="User full name")
@click.option("--email", prompt="Email", help="User email")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="User password",
)
@click.option("--phone", default="", help="Phone number (optional)")
@click.option("--admin", is_flag=True, help="Create as admin user")
def user_create(name, email, password, phone, admin):
    """Create a new user"""
    from app import create_app, db
    from app.models import Permission, Role, User

    app = create_app()
    with app.app_context():
        user = User(
            name=name,
            email=email,
            phone=phone if phone else None,
            is_active=True,
        )
        user.set_password(password)

        if admin:
            admin_role = Role.query.filter_by(name="Admin").first()
            if not admin_role:
                from app.models.rbac import seed_rbac

                seed_rbac(db.session)
                admin_role = Role.query.filter_by(name="Admin").first()
            if admin_role:
                user.roles.append(admin_role)

        db.session.add(user)
        db.session.flush()
        db.session.commit()

        user_type = "admin" if admin else "member"
        click.echo(f"✓ Successfully created {user_type} user: {email}")


@user.command("list")
def user_list():
    """List all users"""
    from app import create_app, db
    from app.models import User

    app = create_app()
    with app.app_context():
        users = User.query.all()

        if not users:
            click.echo("No users found")
            return

        click.echo(
            "\n{:<5} {:<30} {:<25} {:<10} {:<12}".format(
                "ID", "Email", "Name", "Admin", "Membership"
            )
        )
        click.echo("-" * 90)

        for user in users:
            admin_status = "Yes" if any(r.name == "Admin" for r in user.roles) else "No"
            membership = user.membership
            membership_status = membership.status if membership else "None"
            click.echo(
                "{:<5} {:<30} {:<25} {:<10} {:<12}".format(
                    user.id, user.email, user.name[:24], admin_status, membership_status
                )
            )


@user.command("delete")
@click.option("--id", "user_id", prompt="User ID", type=int, help="User ID to delete")
def user_delete(user_id):
    """Delete a user"""
    from app import create_app, db
    from app.models import User

    app = create_app()
    with app.app_context():
        user = User.query.get(user_id)

        if not user:
            click.echo(f"Error: User with ID {user_id} not found")
            return

        if click.confirm(f"Are you sure you want to delete {user.email}?"):
            db.session.delete(user)
            db.session.commit()
            click.echo(f"✓ User {user.email} deleted successfully")
        else:
            click.echo("Cancelled")

# ==============================================================================
# TEST COMMANDS
# ==============================================================================


@cli.group()
def test():
    """Testing commands"""
    pass


@test.command("run")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-c", "--coverage", is_flag=True, help="Run with coverage report")
@click.option("-k", "--keyword", help="Run tests matching keyword")
def test_run(verbose, coverage, keyword):
    """Run test suite"""
    cmd = "pytest"

    if verbose:
        cmd += " -v"

    if coverage:
        cmd += " --cov=app --cov-report=term-missing --no-cov-on-fail"

    if keyword:
        cmd += f' -k "{keyword}"'

    click.echo(f"Running: {cmd}")
    exit_code = os.system(cmd)
    sys.exit(exit_code >> 8)


@test.command("file")
@click.argument("filepath")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def test_file(filepath, verbose):
    """Run specific test file"""
    cmd = f"pytest {filepath}"
    if verbose:
        cmd += " -v"

    click.echo(f"Running: {cmd}")
    exit_code = os.system(cmd)
    sys.exit(exit_code >> 8)


@test.command("coverage")
def test_coverage():
    """Run tests with coverage report"""
    click.echo("Running tests with coverage...")
    os.system("pytest --cov=app --cov-report=term-missing --cov-report=html")
    click.echo("\nHTML coverage report generated in htmlcov/")


# ==============================================================================
# CODE QUALITY COMMANDS
# ==============================================================================


@cli.group()
def lint():
    """Code quality commands"""
    pass


@lint.command("check")
def lint_check():
    """Run linting checks with Ruff"""
    click.echo("Running ruff check...")
    exit_code = os.system("ruff check app/ tests/")
    if exit_code == 0:
        click.echo("✓ Linting passed!")
    else:
        click.echo("\n💡 Tip: Run 'python manage.py lint fix' to auto-fix issues")
    sys.exit(exit_code >> 8)


@lint.command("fix")
def lint_fix():
    """Auto-fix linting issues with Ruff"""
    click.echo("Running ruff check --fix...")
    exit_code = os.system("ruff check --fix app/ tests/")
    if exit_code == 0:
        click.echo("✓ Issues fixed!")
    sys.exit(exit_code >> 8)


@lint.command("format")
@click.option("--check", is_flag=True, help="Check only, do not modify files")
def lint_format(check):
    """Format code with Ruff"""
    if check:
        click.echo("Checking code format with ruff...")
        exit_code = os.system("ruff format --check app/ tests/")
    else:
        click.echo("Formatting code with ruff...")
        exit_code = os.system("ruff format app/ tests/")
        if exit_code == 0:
            click.echo("✓ Code formatted!")
    
    sys.exit(exit_code >> 8)


@lint.command("all")
@click.option("--fix", is_flag=True, help="Auto-fix issues")
def lint_all(fix):
    """Run all linting checks and formatting"""
    click.echo("=== Running Ruff Linting ===")
    if fix:
        exit_code_lint = os.system("ruff check --fix app/ tests/")
    else:
        exit_code_lint = os.system("ruff check app/ tests/")
    
    click.echo("\n=== Running Ruff Format ===")
    if fix:
        exit_code_format = os.system("ruff format app/ tests/")
    else:
        exit_code_format = os.system("ruff format --check app/ tests/")
    
    if exit_code_lint == 0 and exit_code_format == 0:
        click.echo("\n✓ All checks passed!")
        sys.exit(0)
    else:
        if not fix:
            click.echo("\n💡 Tip: Run 'python manage.py lint all --fix' to auto-fix all issues")
        sys.exit(1)


# ==============================================================================
# SHOOT COMMANDS
# ==============================================================================


@cli.group()
def shoot():
    """Shoot management commands"""
    pass


@shoot.command("create")
@click.option("--location", prompt="Location", help="Shooting location")
@click.option("--date", prompt="Date (YYYY-MM-DD HH:MM)", help="Date and time")
@click.option("--capacity", prompt="Capacity", type=int, default=30, help="Capacity")
@click.option("--description", default="", help="Description (optional)")
def shoot_create(location, date, capacity, description):
    """Create a shoot"""
    from app import create_app, db
    from app.models import Shoot

    app = create_app()
    with app.app_context():
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M")
        except ValueError:
            click.echo("Error: Invalid date format. Use YYYY-MM-DD HH:MM")
            return

        shoot_obj = Shoot(
            date=date_obj,
            location=location,
            capacity=capacity,
            description=description if description else None,
        )

        db.session.add(shoot_obj)
        db.session.commit()

        click.echo(f"✓ Shoot created: {location} on {date}")


@shoot.command("list")
@click.option("--upcoming", is_flag=True, help="Show only upcoming shoots")
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
            click.echo("No shoots found")
            return

        click.echo(
            "\n{:<5} {:<20} {:<20} {:<10} {:<10}".format(
                "ID", "Date", "Location", "Capacity", "Bookings"
            )
        )
        click.echo("-" * 70)

        for s in shoots:
            date_str = s.date.strftime("%Y-%m-%d %H:%M")
            bookings = len(s.bookings) if hasattr(s, "bookings") else 0
            click.echo(
                "{:<5} {:<20} {:<20} {:<10} {:<10}".format(
                    s.id, date_str, s.location, s.capacity, bookings
                )
            )


# ==============================================================================
# STATS COMMANDS
# ==============================================================================


@cli.command()
def stats():
    """Show application statistics"""
    from app import create_app, db
    from app.models import Event, Membership, News, Role, Shoot, User

    app = create_app()
    with app.app_context():
        total_users = User.query.count()
        total_admins = db.session.query(User).join(User.roles).filter(Role.name == "Admin").distinct().count()
        total_members = total_users - total_admins
        active_memberships = Membership.query.filter_by(status="active").count()
        upcoming_shoots = Shoot.query.filter(Shoot.date > datetime.now()).count()
        total_news = News.query.count()
        upcoming_events = Event.query.filter(Event.start_date > datetime.now()).count()

        click.echo("\n╔══════════════════════════════════════════╗")
        click.echo("║  South East Archers Statistics          ║")
        click.echo("╠══════════════════════════════════════════╣")
        click.echo(f"║  Total users:           {total_users:>15} ║")
        click.echo(f"║  Members:               {total_members:>15} ║")
        click.echo(f"║  Admins:                {total_admins:>15} ║")
        click.echo(f"║  Active memberships:    {active_memberships:>15} ║")
        click.echo(f"║  Upcoming shoots:       {upcoming_shoots:>15} ║")
        click.echo(f"║  Upcoming events:       {upcoming_events:>15} ║")
        click.echo(f"║  News articles:         {total_news:>15} ║")
        click.echo("╚══════════════════════════════════════════╝\n")


# ==============================================================================
# UTILITY COMMANDS
# ==============================================================================


@cli.command()
def clean():
    """Clean cache and temporary files"""
    import shutil

    patterns = [
        ("__pycache__", "directories"),
        ("*.pyc", "files"),
        (".pytest_cache", "directory"),
        (".coverage", "file"),
        ("htmlcov", "directory"),
    ]

    click.echo("Cleaning up...")

    # Remove __pycache__ directories
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                path = os.path.join(root, d)
                shutil.rmtree(path)
                click.echo(f"  Removed: {path}")

        for f in files:
            if f.endswith(".pyc"):
                path = os.path.join(root, f)
                os.remove(path)
                click.echo(f"  Removed: {path}")

    # Remove specific directories/files
    if os.path.exists(".pytest_cache"):
        shutil.rmtree(".pytest_cache")
        click.echo("  Removed: .pytest_cache")

    if os.path.exists(".coverage"):
        os.remove(".coverage")
        click.echo("  Removed: .coverage")

    if os.path.exists("htmlcov"):
        shutil.rmtree("htmlcov")
        click.echo("  Removed: htmlcov")

    click.echo("✓ Cleanup complete!")


@cli.command()
def install():
    """Install dependencies (Python with UV, Node.js with npm)"""
    click.echo("Installing Python dependencies with UV...")
    exit_code = os.system("uv sync")
    if exit_code != 0:
        click.echo("Failed to install Python dependencies")
        sys.exit(exit_code >> 8)
    
    click.echo("\nInstalling Node.js dependencies...")
    exit_code = os.system("npm ci")
    if exit_code != 0:
        click.echo("Failed to install Node.js dependencies")
        sys.exit(exit_code >> 8)
    
    click.echo("✓ All dependencies installed!")


@cli.group()
def assets():
    """Asset building commands"""
    pass


@assets.command("build")
def assets_build():
    """Build production assets with Vite"""
    click.echo("Building production assets...")
    exit_code = os.system("npm run build")
    if exit_code == 0:
        click.echo("✓ Assets built successfully!")
    sys.exit(exit_code >> 8)


@assets.command("watch")
def assets_watch():
    """Watch and rebuild assets on change"""
    click.echo("Starting Vite dev server...")
    exit_code = os.system("npm run dev")
    sys.exit(exit_code >> 8)


@cli.command()
def dev():
    """Run development servers (Flask + Vite)"""
    import subprocess
    import signal
    
    click.echo("Starting development servers...")
    click.echo("  - Vite dev server (asset hot reloading)")
    click.echo("  - Flask dev server")
    click.echo("\nPress Ctrl+C to stop\n")
    
    processes = []
    
    try:
        # Start Vite dev server
        vite_process = subprocess.Popen(["npm", "run", "dev"])
        processes.append(vite_process)
        
        # Start Flask dev server
        flask_process = subprocess.Popen(["uv", "run", "flask", "run", "--debug"])
        processes.append(flask_process)
        
        # Wait for processes
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        click.echo("\n\nShutting down servers...")
        for p in processes:
            p.terminate()
        click.echo("✓ Servers stopped")


@lint.command("typecheck")
def lint_typecheck():
    """Run mypy type checking"""
    click.echo("Running mypy type checking...")
    exit_code = os.system("mypy app/")
    if exit_code == 0:
        click.echo("✓ Type checking passed!")
    sys.exit(exit_code >> 8)


# ==============================================================================
# SCHEDULER COMMANDS
# ==============================================================================


@cli.group()
def schedule():
    """Task scheduler commands"""
    pass


@schedule.command("run")
def schedule_run():
    """Run scheduled tasks that are due"""
    from app.schedule import schedule as scheduler
    
    click.echo("Running scheduled tasks...")
    scheduler.run_due_tasks()
    click.echo("✓ Scheduled tasks completed")


@schedule.command("list")
def schedule_list():
    """List all scheduled tasks"""
    from app.schedule import schedule as scheduler
    
    events = scheduler.all_events()
    
    if not events:
        click.echo("No scheduled tasks defined")
        return
    
    click.echo("\n{:<40} {:<20}".format("Task", "Schedule"))
    click.echo("-" * 60)
    
    for event in events:
        click.echo("{:<40} {:<20}".format(
            event.description[:39],
            event.expression
        ))
    
    click.echo(f"\nTotal: {len(events)} scheduled tasks")
    click.echo("\nTo run scheduled tasks: python manage.py schedule run")
    click.echo("For production, add to crontab: * * * * * cd /path/to/project && python manage.py schedule run >> /dev/null 2>&1")


@cli.group()
def rbac():
    """RBAC management commands"""
    pass


@rbac.command("seed")
def rbac_seed():
    """Seed default roles and permissions (idempotent)."""
    from app import create_app, db
    from app.models.rbac import seed_rbac

    app = create_app()
    with app.app_context():
        seed_rbac(db.session)
        click.echo("✓ RBAC roles and permissions seeded (idempotent).")


if __name__ == "__main__":
    cli()
