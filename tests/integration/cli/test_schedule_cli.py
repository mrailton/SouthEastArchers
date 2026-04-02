def test_schedule_list_shows_tasks(runner):
    result = runner.invoke(args=["schedule", "list"])
    assert result.exit_code == 0
    # The app has scheduled tasks defined in app/schedule.py
    assert "Task" in result.output
    assert "Schedule" in result.output


def test_schedule_list_shows_total(runner):
    result = runner.invoke(args=["schedule", "list"])
    assert result.exit_code == 0
    assert "Total:" in result.output
