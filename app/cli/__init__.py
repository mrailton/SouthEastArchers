"""Standalone CLI (replaces `flask` commands)."""

from __future__ import annotations

from contextvars import Token

import click
from sqlalchemy.orm import Session

import app.core.config  # noqa: F401 - load .env
from app.core.config import PROJECT_ROOT
from app.db import db, init_db, reset_current_session, set_current_session

ALEMBIC_INI = PROJECT_ROOT / "migrations" / "alembic.ini"

SCHEDULED_JOBS: tuple[str, ...] = (
    "expire-memberships",
    "low-credits-reminder",
)


def _open_cli_session() -> tuple[Session | None, Token | None]:
    from app.db import get_current_session

    try:
        get_current_session()
        return None, None
    except RuntimeError:
        session = db.create_session()
        token = set_current_session(session)
        return session, token


def _close_cli_session(session: Session | None, token: Token | None) -> None:
    if session is not None and token is not None:
        from app.events.background import flush_deferred_handlers

        flush_deferred_handlers()
        session.close()
        reset_current_session(token)


def _resolve_job(job_name: str):
    if job_name == "expire-memberships":
        from app.scheduler.jobs.expire_memberships import expire_memberships

        return expire_memberships
    if job_name == "low-credits-reminder":
        from app.scheduler.jobs.low_credits_reminder import send_low_credits_reminder

        return send_low_credits_reminder
    return None


@click.group()
def cli() -> None:
    """South East Archers management commands."""
    init_db()
    from app.events.handlers import connect_handlers

    connect_handlers()


def main() -> None:
    cli()


@cli.group("db")
def db_cli() -> None:
    """Database migrations."""


@db_cli.command("upgrade")
def db_upgrade() -> None:
    """Run Alembic migrations."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(str(ALEMBIC_INI))
    command.upgrade(alembic_cfg, "head")
    click.echo("✓ Database upgraded.")


@db_cli.command("current")
def db_current() -> None:
    """Show current migration revision."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(str(ALEMBIC_INI))
    command.current(alembic_cfg)


@cli.group("payments")
def payments_cli() -> None:
    """Payment maintenance commands."""


@payments_cli.command("replay-side-effects")
@click.argument("payment_id", type=int)
@click.option("--no-mail", is_flag=True, help="Replay ledger only; skip receipt email.")
def payments_replay_side_effects(payment_id: int, no_mail: bool) -> None:
    """Re-run receipt email and ledger recording for a completed payment."""
    from app.services import payments

    session, token = _open_cli_session()
    try:
        result = payments.replay_completed_payment_side_effects(payment_id, send_mail=not no_mail)
        if not result.success:
            click.echo(f"✗ {result.message}", err=True)
            raise SystemExit(1)
        click.echo(f"✓ {result.message}")
    finally:
        _close_cli_session(session, token)


@cli.group("users")
def users_cli() -> None:
    """User management commands."""


@users_cli.command("create")
def users_create() -> None:
    """Interactively create a new user."""
    from app.repositories import RBACRepository
    from app.services import users

    session, token = _open_cli_session()
    try:
        click.echo("=== Create New User ===\n")

        name = click.prompt("Full name")
        email = click.prompt("Email address")
        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
        phone = click.prompt("Phone number (optional)", default="", show_default=False)

        # Role selection
        roles = RBACRepository.list_roles()
        selected_role_ids: list[int] = []
        if roles:
            click.echo("\nAvailable roles:")
            for role in roles:
                click.echo(f"  [{role.id}] {role.name}" + (f" — {role.description}" if role.description else ""))
            raw = click.prompt("\nEnter role IDs to assign (comma-separated, or blank for none)", default="", show_default=False)
            if raw.strip():
                valid_ids = {r.id for r in roles}
                for part in raw.split(","):
                    part = part.strip()
                    if part.isdigit() and int(part) in valid_ids:
                        selected_role_ids.append(int(part))
                    elif part:
                        click.echo(f"  ⚠ Skipping unknown role ID: {part}", err=True)

        activate = click.confirm("\nActivate account immediately?", default=False)
        create_membership = click.confirm("Create membership?", default=False)

        result = users.create_member(
            name=name,
            email=email,
            phone=phone or None,
            password=password,
            role_ids=selected_role_ids or None,
            create_membership=create_membership,
        )

        if not result.success:
            click.echo(f"\n✗ {result.message}", err=True)
            raise SystemExit(1)

        user = result.data
        if activate and user and not user.is_active:
            users.activate_account(user.id)

        click.echo(f"\n✓ User '{name}' ({email}) created successfully.")
        if selected_role_ids:
            assigned = [r.name for r in roles if r.id in selected_role_ids]
            click.echo(f"  Roles: {', '.join(assigned)}")
        if activate:
            click.echo("  Account: active")
        if create_membership:
            click.echo("  Membership: created")
    finally:
        _close_cli_session(session, token)


@cli.group("rbac")
def rbac_cli() -> None:
    """RBAC management."""


@rbac_cli.command("seed")
def rbac_seed() -> None:
    """Seed default roles and permissions (idempotent)."""
    from app.repositories import RBACRepository

    session, token = _open_cli_session()
    try:
        RBACRepository.seed()
        click.echo("✓ RBAC roles and permissions seeded (idempotent).")
    finally:
        _close_cli_session(session, token)


@cli.group("scheduler")
def scheduler_cli() -> None:
    """Scheduled maintenance jobs (intended for external cron)."""


@scheduler_cli.command("list")
def scheduler_list() -> None:
    """List available scheduled jobs."""
    for name in SCHEDULED_JOBS:
        click.echo(name)


@scheduler_cli.command("run")
@click.argument("job_name")
def scheduler_run(job_name: str) -> None:
    """Run a scheduled job by name."""
    from app.routes_map import FALLBACK_ROUTES
    from app.templating import register_route_names, setup_template_globals

    job = _resolve_job(job_name)
    if job is None:
        click.echo(f"Unknown job: {job_name}")
        click.echo(f"Available jobs: {', '.join(SCHEDULED_JOBS)}")
        raise SystemExit(1)

    register_route_names([type("Route", (), {"name": name, "path": path})() for name, path in FALLBACK_ROUTES.items()])
    setup_template_globals()

    session, token = _open_cli_session()
    try:
        job()  # type: ignore[operator]
    finally:
        _close_cli_session(session, token)
