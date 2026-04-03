"""CLI commands for South East Archers, registered on the Flask app."""


def register_commands(app):
    """Register all CLI commands on the Flask app."""
    from .rbac import rbac_cli
    from .schedule import schedule_cli
    from .shoot import shoot_cli
    from .user import user_cli
    from .utils import db_reset, stats

    app.cli.add_command(user_cli)
    app.cli.add_command(shoot_cli)
    app.cli.add_command(schedule_cli)
    app.cli.add_command(rbac_cli)
    app.cli.add_command(stats)
    app.cli.add_command(db_reset)
