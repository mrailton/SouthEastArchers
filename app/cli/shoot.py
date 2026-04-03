"""Shoot management CLI commands."""

from datetime import datetime

import click
from flask.cli import AppGroup

shoot_cli = AppGroup("shoot", help="Shoot management commands")

VALID_LOCATIONS = ["Hall", "Meadow", "Woods"]


@shoot_cli.command("create")
@click.option("--location", prompt="Location (Hall/Meadow/Woods)", type=click.Choice(VALID_LOCATIONS, case_sensitive=False), help="Shooting location")
@click.option("--date", prompt="Date (YYYY-MM-DD)", help="Shoot date")
@click.option("--description", default="", help="Description (optional)")
def shoot_create(location, date, description):
    """Create a shoot"""
    from app.models import Shoot
    from app.models.shoot import ShootLocation
    from app.repositories import ShootRepository

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        click.echo("Error: Invalid date format. Use YYYY-MM-DD")
        return

    shoot_obj = Shoot(
        date=date_obj,
        location=ShootLocation(location),
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

    click.echo("\n{:<5} {:<15} {:<15} {:<10}".format("ID", "Date", "Location", "Visitors"))
    click.echo("-" * 50)

    for s in shoots:
        date_str = s.date.strftime("%Y-%m-%d")
        location = s.location.value if s.location else ""
        visitors = len(s.visitors) if s.visitors else 0
        click.echo(f"{s.id:<5} {date_str:<15} {location:<15} {visitors:<10}")
