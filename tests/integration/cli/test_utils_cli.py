from datetime import date, timedelta
from unittest.mock import patch

from app import db
from app.models import News, Shoot
from app.models.shoot import ShootLocation


def test_stats_empty_database(runner):
    result = runner.invoke(args=["stats"])
    assert result.exit_code == 0
    assert "South East Archers Statistics" in result.output
    assert "Total users:" in result.output


def test_stats_with_data(runner, test_user, admin_user):
    # test_user has an active membership, admin_user does not
    result = runner.invoke(args=["stats"])
    assert result.exit_code == 0
    assert "Total users:" in result.output
    assert "Members:" in result.output
    assert "Admins:" in result.output
    assert "Active memberships:" in result.output


def test_stats_counts_upcoming_shoots(runner):
    future_shoot = Shoot(date=date.today() + timedelta(days=7), location=ShootLocation.HALL)
    past_shoot = Shoot(date=date.today() - timedelta(days=7), location=ShootLocation.MEADOW)
    db.session.add_all([future_shoot, past_shoot])
    db.session.commit()

    result = runner.invoke(args=["stats"])
    assert result.exit_code == 0
    assert "Upcoming shoots:" in result.output


def test_stats_counts_news(runner):
    news = News(title="Test", summary="Summary", content="Content")
    db.session.add(news)
    db.session.commit()

    result = runner.invoke(args=["stats"])
    assert result.exit_code == 0
    assert "News articles:" in result.output


@patch("app.repositories.base.BaseRepository.create_all")
@patch("app.repositories.base.BaseRepository.drop_all")
def test_db_reset_confirmed(mock_drop, mock_create, runner):
    """db-reset with 'y' confirmation should complete."""
    result = runner.invoke(args=["db-reset"], input="y\n")
    assert result.exit_code == 0
    assert "Dropping all tables" in result.output
    assert "Creating all tables" in result.output
    assert "Database reset complete" in result.output
    mock_drop.assert_called_once()
    mock_create.assert_called_once()


def test_db_reset_declined(runner):
    """db-reset with 'n' should abort without changes."""
    result = runner.invoke(args=["db-reset"], input="n\n")
    assert result.exit_code == 0
    assert "Database reset complete" not in result.output
