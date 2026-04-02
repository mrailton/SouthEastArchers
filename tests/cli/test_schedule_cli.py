"""Tests for schedule management CLI commands."""


class TestScheduleList:
    def test_schedule_list_shows_tasks(self, runner):
        result = runner.invoke(args=["schedule", "list"])
        assert result.exit_code == 0
        # The app has scheduled tasks defined in app/schedule.py
        assert "Task" in result.output
        assert "Schedule" in result.output

    def test_schedule_list_shows_total(self, runner):
        result = runner.invoke(args=["schedule", "list"])
        assert result.exit_code == 0
        assert "Total:" in result.output
