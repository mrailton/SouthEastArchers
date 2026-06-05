"""Standalone CLI (replaces `flask` commands)."""

from __future__ import annotations

import click

import app.core.config  # noqa: F401 - load .env
from app.db import init_db


@click.group()
def cli() -> None:
    """South East Archers management commands."""
    init_db()


@cli.group("db")
def db_cli() -> None:
    """Database migrations."""


@db_cli.command("upgrade")
def db_upgrade() -> None:
    """Run Alembic migrations."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("migrations/alembic.ini")
    command.upgrade(alembic_cfg, "head")
    click.echo("✓ Database upgraded.")


@db_cli.command("current")
def db_current() -> None:
    """Show current migration revision."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("migrations/alembic.ini")
    command.current(alembic_cfg)


@cli.group("rbac")
def rbac_cli() -> None:
    """RBAC management."""


@rbac_cli.command("seed")
def rbac_seed() -> None:
    """Seed default roles and permissions (idempotent)."""
    from app.repositories import RBACRepository

    RBACRepository.seed()
    click.echo("✓ RBAC roles and permissions seeded (idempotent).")
