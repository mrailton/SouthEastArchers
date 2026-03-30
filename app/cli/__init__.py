"""CLI commands for South East Archers, registered on the Flask app."""

import click
from flask import current_app
from flask.cli import AppGroup, with_appcontext


def register_commands(app):
    """Register all CLI commands on the Flask app."""
    from .assets import assets_cli
    from .lint import lint_cli
    from .rbac import rbac_cli
    from .schedule import schedule_cli
    from .shoot import shoot_cli
    from .testing import test_cli
    from .user import user_cli
    from .utils import clean, db_reset, dev, install, stats

    app.cli.add_command(user_cli)
    app.cli.add_command(test_cli)
    app.cli.add_command(lint_cli)
    app.cli.add_command(shoot_cli)
    app.cli.add_command(assets_cli)
    app.cli.add_command(schedule_cli)
    app.cli.add_command(rbac_cli)
    app.cli.add_command(stats)
    app.cli.add_command(clean)
    app.cli.add_command(install)
    app.cli.add_command(dev)
    app.cli.add_command(db_reset)
