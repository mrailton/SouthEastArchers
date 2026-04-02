"""Tests for utility CLI commands: stats, clean, install, db-reset."""

from datetime import date, timedelta
from unittest.mock import patch

from app import db
from app.models import News, Shoot
from app.models.shoot import ShootLocation


class TestStats:
    def test_stats_empty_database(self, runner):
        result = runner.invoke(args=["stats"])
        assert result.exit_code == 0
        assert "South East Archers Statistics" in result.output
        assert "Total users:" in result.output

    def test_stats_with_data(self, runner, test_user, admin_user):
        # test_user has an active membership, admin_user does not
        result = runner.invoke(args=["stats"])
        assert result.exit_code == 0
        assert "Total users:" in result.output
        assert "Members:" in result.output
        assert "Admins:" in result.output
        assert "Active memberships:" in result.output

    def test_stats_counts_upcoming_shoots(self, runner):
        future_shoot = Shoot(date=date.today() + timedelta(days=7), location=ShootLocation.HALL)
        past_shoot = Shoot(date=date.today() - timedelta(days=7), location=ShootLocation.MEADOW)
        db.session.add_all([future_shoot, past_shoot])
        db.session.commit()

        result = runner.invoke(args=["stats"])
        assert result.exit_code == 0
        assert "Upcoming shoots:" in result.output

    def test_stats_counts_news(self, runner):
        news = News(title="Test", summary="Summary", content="Content")
        db.session.add(news)
        db.session.commit()

        result = runner.invoke(args=["stats"])
        assert result.exit_code == 0
        assert "News articles:" in result.output


class TestClean:
    def test_clean_runs_successfully(self, runner, tmp_path, monkeypatch):
        """clean should complete without errors when run in a temp directory."""
        monkeypatch.chdir(tmp_path)

        # Create some cache files to clean
        pycache = tmp_path / "subdir" / "__pycache__"
        pycache.mkdir(parents=True)
        (pycache / "module.cpython-314.pyc").write_text("")

        pyc_file = tmp_path / "old.pyc"
        pyc_file.write_text("")

        pytest_cache = tmp_path / ".pytest_cache"
        pytest_cache.mkdir()

        coverage_file = tmp_path / ".coverage"
        coverage_file.write_text("")

        htmlcov = tmp_path / "htmlcov"
        htmlcov.mkdir()

        result = runner.invoke(args=["clean"])
        assert result.exit_code == 0
        assert "Cleanup complete!" in result.output

        assert not pycache.exists()
        assert not pyc_file.exists()
        assert not pytest_cache.exists()
        assert not coverage_file.exists()
        assert not htmlcov.exists()

    def test_clean_handles_empty_directory(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(args=["clean"])
        assert result.exit_code == 0
        assert "Cleanup complete!" in result.output


class TestDbReset:
    @patch("app.repositories.base.BaseRepository.create_all")
    @patch("app.repositories.base.BaseRepository.drop_all")
    def test_db_reset_confirmed(self, mock_drop, mock_create, runner):
        """db-reset with 'y' confirmation should complete."""
        result = runner.invoke(args=["db-reset"], input="y\n")
        assert result.exit_code == 0
        assert "Dropping all tables" in result.output
        assert "Creating all tables" in result.output
        assert "Database reset complete" in result.output
        mock_drop.assert_called_once()
        mock_create.assert_called_once()

    def test_db_reset_declined(self, runner):
        """db-reset with 'n' should abort without changes."""
        result = runner.invoke(args=["db-reset"], input="n\n")
        assert result.exit_code == 0
        assert "Database reset complete" not in result.output


class TestInstall:
    @patch("app.cli.utils.os.system", return_value=0)
    def test_install_success(self, mock_system, runner):
        result = runner.invoke(args=["install"])
        assert "Installing Python dependencies" in result.output
        assert "Installing Node.js dependencies" in result.output
        assert "All dependencies installed!" in result.output
        assert mock_system.call_count == 2

    @patch("app.cli.utils.os.system", side_effect=[256, 0])
    def test_install_python_failure(self, mock_system, runner):
        result = runner.invoke(args=["install"])
        assert "Failed to install Python dependencies" in result.output

    @patch("app.cli.utils.os.system", side_effect=[0, 256])
    def test_install_node_failure(self, mock_system, runner):
        result = runner.invoke(args=["install"])
        assert "Failed to install Node.js dependencies" in result.output
