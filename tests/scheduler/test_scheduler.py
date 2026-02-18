"""Tests for the task scheduler."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.scheduler import Event, Schedule

# Event tests

def test_event_creation():
    """Test creating a basic event"""
    callback = Mock()
    event = Event(callback, "Test event")

    assert event.callback == callback
    assert event.description == "Test event"
    assert event.expression == "* * * * *"  # Default: every minute


def test_event_without_description_uses_callback_name():
    """Test event uses callback name when no description provided"""

    def my_task():
        pass

    event = Event(my_task)
    assert event.description == "my_task"


def test_cron_expression():
    """Test setting custom cron expression"""
    callback = Mock()
    event = Event(callback).cron("0 0 * * *")

    assert event.expression == "0 0 * * *"


def test_every_minute():
    """Test every_minute schedule"""
    event = Event(Mock()).every_minute()
    assert event.expression == "* * * * *"


def test_every_five_minutes():
    """Test every_five_minutes schedule"""
    event = Event(Mock()).every_five_minutes()
    assert event.expression == "*/5 * * * *"


def test_every_ten_minutes():
    """Test every_ten_minutes schedule"""
    event = Event(Mock()).every_ten_minutes()
    assert event.expression == "*/10 * * * *"


def test_every_fifteen_minutes():
    """Test every_fifteen_minutes schedule"""
    event = Event(Mock()).every_fifteen_minutes()
    assert event.expression == "*/15 * * * *"


def test_every_thirty_minutes():
    """Test every_thirty_minutes schedule"""
    event = Event(Mock()).every_thirty_minutes()
    assert event.expression == "*/30 * * * *"


def test_hourly():
    """Test hourly schedule"""
    event = Event(Mock()).hourly()
    assert event.expression == "0 * * * *"


def test_hourly_at():
    """Test hourly_at schedule"""
    event = Event(Mock()).hourly_at(15)
    assert event.expression == "15 * * * *"


def test_daily():
    """Test daily schedule (midnight)"""
    event = Event(Mock()).daily()
    assert event.expression == "0 0 * * *"


def test_daily_at():
    """Test daily_at schedule"""
    event = Event(Mock()).daily_at("13:30")
    assert event.expression == "30 13 * * *"


def test_weekly():
    """Test weekly schedule (Sunday at midnight)"""
    event = Event(Mock()).weekly()
    assert event.expression == "0 0 * * 0"


def test_weekly_on():
    """Test weekly_on schedule (Monday at 9am)"""
    event = Event(Mock()).weekly_on(1, "09:00")
    assert event.expression == "0 9 * * 1"


def test_monthly():
    """Test monthly schedule (1st at midnight)"""
    event = Event(Mock()).monthly()
    assert event.expression == "0 0 1 * *"


def test_monthly_on():
    """Test monthly_on schedule (15th at 2pm)"""
    event = Event(Mock()).monthly_on(15, "14:00")
    assert event.expression == "0 14 15 * *"


def test_yearly():
    """Test yearly schedule (Jan 1st at midnight)"""
    event = Event(Mock()).yearly()
    assert event.expression == "0 0 1 1 *"


def test_is_due_every_minute():
    """Test is_due for every minute schedule"""
    event = Event(Mock()).every_minute()

    # Should be due at any time
    assert event.is_due(datetime(2024, 1, 15, 10, 30))
    assert event.is_due(datetime(2024, 6, 20, 15, 45))


def test_is_due_hourly():
    """Test is_due for hourly schedule"""
    event = Event(Mock()).hourly()

    # Should be due at minute 0
    assert event.is_due(datetime(2024, 1, 15, 10, 0))
    assert event.is_due(datetime(2024, 1, 15, 15, 0))

    # Should not be due at other minutes
    assert not event.is_due(datetime(2024, 1, 15, 10, 30))
    assert not event.is_due(datetime(2024, 1, 15, 15, 15))


def test_is_due_daily_at():
    """Test is_due for daily_at schedule"""
    event = Event(Mock()).daily_at("13:30")

    # Should be due at 13:30
    assert event.is_due(datetime(2024, 1, 15, 13, 30))
    assert event.is_due(datetime(2024, 6, 20, 13, 30))

    # Should not be due at other times
    assert not event.is_due(datetime(2024, 1, 15, 13, 31))
    assert not event.is_due(datetime(2024, 1, 15, 14, 30))


def test_is_due_every_five_minutes():
    """Test is_due for every 5 minutes schedule"""
    event = Event(Mock()).every_five_minutes()

    # Should be due at minutes divisible by 5
    assert event.is_due(datetime(2024, 1, 15, 10, 0))
    assert event.is_due(datetime(2024, 1, 15, 10, 5))
    assert event.is_due(datetime(2024, 1, 15, 10, 10))
    assert event.is_due(datetime(2024, 1, 15, 10, 15))

    # Should not be due at other minutes
    assert not event.is_due(datetime(2024, 1, 15, 10, 1))
    assert not event.is_due(datetime(2024, 1, 15, 10, 7))
    assert not event.is_due(datetime(2024, 1, 15, 10, 13))


def test_weekdays_constraint():
    """Test weekdays constraint"""
    event = Event(Mock()).daily().weekdays()

    # Monday (0) through Friday (4) should be due
    assert event.is_due(datetime(2024, 1, 15, 0, 0))  # Monday
    assert event.is_due(datetime(2024, 1, 16, 0, 0))  # Tuesday
    assert event.is_due(datetime(2024, 1, 17, 0, 0))  # Wednesday
    assert event.is_due(datetime(2024, 1, 18, 0, 0))  # Thursday
    assert event.is_due(datetime(2024, 1, 19, 0, 0))  # Friday

    # Saturday (5) and Sunday (6) should not be due
    assert not event.is_due(datetime(2024, 1, 20, 0, 0))  # Saturday
    assert not event.is_due(datetime(2024, 1, 21, 0, 0))  # Sunday


def test_weekends_constraint():
    """Test weekends constraint"""
    event = Event(Mock()).daily().weekends()

    # Saturday and Sunday should be due
    assert event.is_due(datetime(2024, 1, 20, 0, 0))  # Saturday
    assert event.is_due(datetime(2024, 1, 21, 0, 0))  # Sunday

    # Weekdays should not be due
    assert not event.is_due(datetime(2024, 1, 15, 0, 0))  # Monday
    assert not event.is_due(datetime(2024, 1, 19, 0, 0))  # Friday


def test_mondays_constraint():
    """Test mondays constraint"""
    event = Event(Mock()).daily().mondays()

    assert event.is_due(datetime(2024, 1, 15, 0, 0))  # Monday
    assert not event.is_due(datetime(2024, 1, 16, 0, 0))  # Tuesday


def test_tuesdays_constraint():
    """Test tuesdays constraint"""
    event = Event(Mock()).daily().tuesdays()

    assert event.is_due(datetime(2024, 1, 16, 0, 0))  # Tuesday
    assert not event.is_due(datetime(2024, 1, 15, 0, 0))  # Monday


def test_when_constraint():
    """Test when constraint with custom callback"""
    condition = Mock(return_value=True)
    event = Event(Mock()).daily().when(condition)

    assert event.is_due(datetime(2024, 1, 15, 0, 0))
    condition.assert_called()

    # Change condition to False
    condition.return_value = False
    assert not event.is_due(datetime(2024, 1, 15, 0, 0))


def test_skip_constraint():
    """Test skip constraint with custom callback"""
    should_skip = Mock(return_value=False)
    event = Event(Mock()).daily().skip(should_skip)

    # Should be due when skip returns False
    assert event.is_due(datetime(2024, 1, 15, 0, 0))
    should_skip.assert_called()

    # Should not be due when skip returns True
    should_skip.return_value = True
    assert not event.is_due(datetime(2024, 1, 15, 0, 0))


def test_multiple_constraints():
    """Test combining multiple constraints"""
    event = Event(Mock()).daily_at("09:00").weekdays()

    # Should be due on weekday at 9am
    assert event.is_due(datetime(2024, 1, 15, 9, 0))  # Monday 9am

    # Should not be due on weekend at 9am
    assert not event.is_due(datetime(2024, 1, 20, 9, 0))  # Saturday 9am

    # Should not be due on weekday at wrong time
    assert not event.is_due(datetime(2024, 1, 15, 10, 0))  # Monday 10am


def test_run_executes_callback():
    """Test that run executes the callback"""
    callback = Mock()
    event = Event(callback, "Test")

    event.run()

    callback.assert_called_once()


def test_run_handles_exceptions():
    """Test that run handles exceptions gracefully"""
    callback = Mock(side_effect=Exception("Test error"))
    event = Event(callback, "Test")

    with pytest.raises(Exception, match="Test error"):
        event.run()


def test_chaining_methods():
    """Test that methods can be chained"""
    callback = Mock()
    event = Event(callback).daily().weekdays().when(lambda: True)

    assert event.expression == "0 0 * * *"
    assert len(event._filters) == 1  # weekdays
    assert len(event._filters_no_arg) == 1  # when


# Schedule tests

def test_schedule_creation():
    """Test creating a schedule"""
    schedule = Schedule()
    assert schedule._events == []


def test_call_adds_event():
    """Test that call() adds an event"""
    schedule = Schedule()
    callback = Mock()

    event = schedule.call(callback, "Test task")

    assert len(schedule._events) == 1
    assert schedule._events[0] == event
    assert event.description == "Test task"


def test_call_uses_callback_name_when_no_description():
    """Test call() uses callback name when no description"""
    schedule = Schedule()

    def my_function():
        pass

    event = schedule.call(my_function)

    assert event.description == "my_function"


def test_command_creates_event():
    """Test that command() creates an event"""
    schedule = Schedule()

    event = schedule.command("db upgrade", "Upgrade database")

    assert len(schedule._events) == 1
    assert event.description == "Upgrade database"


def test_command_executes_management_command():
    """Test that command() executes the management command"""
    schedule = Schedule()

    event = schedule.command("test command", "Test")

    with patch("os.system") as mock_system:
        event.run()
        mock_system.assert_called_once_with("python manage.py test command")


def test_due_events_returns_due_tasks():
    """Test due_events returns only tasks that are due"""
    schedule = Schedule()

    # Create tasks with different schedules
    schedule.call(Mock(), "Every minute").every_minute()
    schedule.call(Mock(), "Daily at noon").daily_at("12:00")
    schedule.call(Mock(), "Hourly").hourly()

    # At 12:00, all three tasks should be due
    due = schedule.due_events(datetime(2024, 1, 15, 12, 0))
    assert len(due) == 3

    # At 12:30, only one task should be due (every minute)
    due = schedule.due_events(datetime(2024, 1, 15, 12, 30))
    assert len(due) == 1


def test_run_due_tasks_executes_due_tasks():
    """Test run_due_tasks executes all due tasks"""
    schedule = Schedule()

    callback1 = Mock()
    callback2 = Mock()
    callback3 = Mock()

    schedule.call(callback1, "Task 1").daily_at("10:00")
    schedule.call(callback2, "Task 2").daily_at("10:00")
    schedule.call(callback3, "Task 3").daily_at("11:00")

    # At 10:00, tasks 1 and 2 should run
    schedule.run_due_tasks(datetime(2024, 1, 15, 10, 0))

    callback1.assert_called_once()
    callback2.assert_called_once()
    callback3.assert_not_called()


def test_run_due_tasks_continues_on_error():
    """Test run_due_tasks continues if one task fails"""
    schedule = Schedule()

    callback1 = Mock(side_effect=Exception("Task 1 failed"))
    callback2 = Mock()

    schedule.call(callback1, "Task 1").every_minute()
    schedule.call(callback2, "Task 2").every_minute()

    # Both tasks should be attempted
    schedule.run_due_tasks(datetime(2024, 1, 15, 10, 0))

    callback1.assert_called_once()
    callback2.assert_called_once()


def test_all_events_returns_all_events():
    """Test all_events returns all registered events"""
    schedule = Schedule()

    schedule.call(Mock(), "Task 1").daily()
    schedule.call(Mock(), "Task 2").hourly()
    schedule.call(Mock(), "Task 3").weekly()

    events = schedule.all_events()
    assert len(events) == 3


def test_complex_scheduling_scenario():
    """Test a complex real-world scheduling scenario"""
    schedule = Schedule()

    # Daily cleanup at 2am
    cleanup = Mock()
    schedule.call(cleanup, "Daily cleanup").daily_at("02:00")

    # Send reminders every Monday at 9am
    reminders = Mock()
    schedule.call(reminders, "Weekly reminders").weekly_on(1, "09:00")

    # Sync data every 15 minutes on weekdays
    sync = Mock()
    schedule.call(sync, "Sync data").every_fifteen_minutes().weekdays()

    # Test Monday 9:00am (should have weekly reminders + sync)
    monday_9am = datetime(2024, 1, 15, 9, 0)  # Monday
    due = schedule.due_events(monday_9am)
    descriptions = [e.description for e in due]

    assert "Weekly reminders" in descriptions
    assert "Sync data" in descriptions
    assert len(due) == 2

    # Test Monday 9:15am (should have only sync, not reminders)
    monday_915am = datetime(2024, 1, 15, 9, 15)  # Monday
    due = schedule.due_events(monday_915am)
    descriptions = [e.description for e in due]

    assert "Sync data" in descriptions
    assert "Weekly reminders" not in descriptions

    # Test Saturday 9:15am (weekend)
    saturday_915am = datetime(2024, 1, 20, 9, 15)  # Saturday
    due = schedule.due_events(saturday_915am)

    # Should not have sync (weekdays only)
    descriptions = [e.description for e in due]
    assert "Sync data" not in descriptions

    # Test Tuesday 2:00am
    tuesday_2am = datetime(2024, 1, 16, 2, 0)  # Tuesday
    due = schedule.due_events(tuesday_2am)
    descriptions = [e.description for e in due]

    # Should have: daily cleanup + sync (0 is divisible by 15)
    assert "Daily cleanup" in descriptions
    assert "Sync data" in descriptions
