"""Utility CLI commands: stats, clean, install, dev, db-reset."""

import os
import shutil
import subprocess
import sys
from datetime import datetime

import click
from flask.cli import with_appcontext


@click.command()
@with_appcontext
def stats():
    """Show application statistics"""
    from app import db
    from app.models import Event, Membership, News, Role, Shoot, User

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


@click.command()
def clean():
    """Clean cache and temporary files"""
    click.echo("Cleaning up...")

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


@click.command()
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


@click.command()
def dev():
    """Run development servers (Flask + Vite)"""
    static_dir = os.path.join("resources", "static")
    images_link = os.path.join(static_dir, "images")
    os.makedirs(static_dir, exist_ok=True)
    if not os.path.exists(images_link):
        os.symlink(os.path.join("..", "assets", "images"), images_link)

    click.echo("Starting development servers...")
    click.echo("  - Vite dev server (asset hot reloading)")
    click.echo("  - Flask dev server")
    click.echo("\nPress Ctrl+C to stop\n")

    processes = []

    try:
        vite_process = subprocess.Popen(["npm", "run", "dev"])
        processes.append(vite_process)

        flask_process = subprocess.Popen(["uv", "run", "flask", "run", "--debug"])
        processes.append(flask_process)

        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        click.echo("\n\nShutting down servers...")
        for p in processes:
            p.terminate()
        click.echo("✓ Servers stopped")


@click.command("db-reset")
@with_appcontext
def db_reset():
    """Reset database (WARNING: Deletes all data)"""
    if click.confirm("WARNING: This will delete all data. Continue?"):
        from app import db

        click.echo("Dropping all tables...")
        db.drop_all()
        click.echo("Creating all tables...")
        db.create_all()
        click.echo("Database reset complete!")
