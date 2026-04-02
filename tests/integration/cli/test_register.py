def test_all_commands_registered(app):
    """All CLI command groups and standalone commands should be registered."""
    commands = app.cli.list_commands(None)
    expected = ["user", "shoot", "schedule", "rbac", "stats", "db-reset"]
    for name in expected:
        assert name in commands, f"Command '{name}' not registered"
