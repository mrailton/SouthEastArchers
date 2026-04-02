"""RBAC management CLI commands."""

import click
from flask.cli import AppGroup

rbac_cli = AppGroup("rbac", help="RBAC management commands")


@rbac_cli.command("seed")
def rbac_seed():
    """Seed default roles and permissions (idempotent)."""
    from app.repositories import RBACRepository

    RBACRepository.seed()
    click.echo("✓ RBAC roles and permissions seeded (idempotent).")
