"""Utility CLI commands: stats, db-reset."""

import click
from flask.cli import with_appcontext


@click.command()
@with_appcontext
def stats():
    """Show application statistics"""
    from app.repositories import EventRepository, MembershipRepository, NewsRepository, ShootRepository, UserRepository

    total_users = UserRepository.count()
    total_admins = UserRepository.count_admins()
    total_members = total_users - total_admins
    active_memberships = MembershipRepository.count_active()
    upcoming_shoots = ShootRepository.count_upcoming()
    total_news = NewsRepository.count()
    upcoming_events = EventRepository.count_upcoming()

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


@click.command("db-reset")
@with_appcontext
def db_reset():
    """Reset database (WARNING: Deletes all data)"""
    if click.confirm("WARNING: This will delete all data. Continue?"):
        from app.repositories import BaseRepository

        click.echo("Dropping all tables...")
        BaseRepository.drop_all()
        click.echo("Creating all tables...")
        BaseRepository.create_all()
        click.echo("Database reset complete!")
