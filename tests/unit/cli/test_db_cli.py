from unittest.mock import patch

from app.cli import cli


@patch("alembic.command.upgrade")
def test_db_upgrade_cli(mock_upgrade, runner):
    result = runner.invoke(cli, ["db", "upgrade"])

    assert result.exit_code == 0
    assert "Database upgraded" in result.output
    mock_upgrade.assert_called_once()


@patch("alembic.command.current")
def test_db_current_cli(mock_current, runner):
    result = runner.invoke(cli, ["db", "current"])

    assert result.exit_code == 0
    mock_current.assert_called_once()
