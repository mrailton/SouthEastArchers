"""RBAC management CLI commands."""

import click
from flask.cli import AppGroup

from app import db

rbac_cli = AppGroup("rbac", help="RBAC management commands")


@rbac_cli.command("seed")
def rbac_seed():
    """Seed default roles and permissions (idempotent)."""
    from app.models.rbac import seed_rbac

    seed_rbac(db.session)
    click.echo("✓ RBAC roles and permissions seeded (idempotent).")
