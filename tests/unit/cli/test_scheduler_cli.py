from unittest.mock import MagicMock, patch

from app.cli import cli


def test_scheduler_list(runner):
    result = runner.invoke(cli, ["scheduler", "list"])
    assert result.exit_code == 0
    assert "expire-memberships" in result.output
    assert "low-credits-reminder" in result.output


def test_scheduler_run_unknown_job(runner):
    result = runner.invoke(cli, ["scheduler", "run", "nonexistent"])
    assert result.exit_code == 1
    assert "Unknown job" in result.output


@patch("app.cli._resolve_job")
def test_scheduler_run_expire_memberships(mock_resolve, runner, app):
    mock_job = MagicMock()
    mock_resolve.return_value = mock_job
    result = runner.invoke(cli, ["scheduler", "run", "expire-memberships"])
    assert result.exit_code == 0
    mock_resolve.assert_called_once_with("expire-memberships")
    mock_job.assert_called_once()
