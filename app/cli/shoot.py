"""Shoot management CLI commands."""

from datetime import datetime

import click
from flask.cli import AppGroup

shoot_cli = AppGroup("shoot", help="Shoot management commands")


@shoot_cli.command("create")
@click.option("--location", prompt="Location", help="Shooting location")
@click.option("--date", prompt="Date (YYYY-MM-DD HH:MM)", help="Date and time")
@click.option("--capacity", prompt="Capacity", type=int, default=30, help="Capacity")
@click.option("--description", default="", help="Description (optional)")
def shoot_create(location, date, capacity, description):
    """Create a shoot"""
    from app.models import Shoot
    from app.repositories import ShootRepository

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

    ShootRepository.add(shoot_obj)
    ShootRepository.save()

    click.echo(f"✓ Shoot created: {location} on {date}")


@shoot_cli.command("list")
@click.option("--upcoming", is_flag=True, help="Show only upcoming shoots")
def shoot_list(upcoming):
    """List shoots"""
    from app.repositories import ShootRepository

    shoots = ShootRepository.get_upcoming() if upcoming else ShootRepository.get_all()

    if not shoots:
        click.echo("No shoots found")
        return

    click.echo("\n{:<5} {:<20} {:<20} {:<10} {:<10}".format("ID", "Date", "Location", "Capacity", "Bookings"))
    click.echo("-" * 70)

    for s in shoots:
        date_str = s.date.strftime("%Y-%m-%d %H:%M")
        bookings = len(s.bookings) if hasattr(s, "bookings") else 0
        click.echo(f"{s.id:<5} {date_str:<20} {s.location:<20} {s.capacity:<10} {bookings:<10}")
