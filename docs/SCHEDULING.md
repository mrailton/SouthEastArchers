# Task Scheduling

This application includes a Laravel-style task scheduler that allows you to define scheduled tasks in code and run them via a single cron job.

## Overview

The scheduler provides a fluent API for defining tasks that should run on a schedule. Instead of managing multiple cron jobs, you define all your scheduled tasks in `app/schedule.py` and set up a single cron entry.

## Quick Start

### 1. Define Your Tasks

Edit `app/schedule.py` to define your scheduled tasks:

```python
from app.scheduler import schedule

def my_task():
    print("Task running!")

# Run every day at 2am
schedule.call(my_task, "My daily task").daily_at("02:00")

# Run every 5 minutes
schedule.call(another_task, "Frequent task").every_five_minutes()

# Run management command weekly
schedule.command("db backup", "Weekly backup").weekly()
```

### 2. Test Locally

List all scheduled tasks:
```bash
python manage.py schedule list
```

Run tasks that are due now:
```bash
python manage.py schedule run
```

### 3. Set Up Cron Job

Add this single line to your crontab (runs every minute):

```bash
* * * * * cd /path/to/SouthEastArchers && /path/to/python manage.py schedule run >> /dev/null 2>&1
```

To edit your crontab:
```bash
crontab -e
```

For logging output to a file instead:
```bash
* * * * * cd /path/to/SouthEastArchers && /path/to/python manage.py schedule run >> /var/log/scheduler.log 2>&1
```

## Available Methods

### Frequency Methods

```python
# Time-based
schedule.call(task).every_minute()
schedule.call(task).every_five_minutes()
schedule.call(task).every_ten_minutes()
schedule.call(task).every_fifteen_minutes()
schedule.call(task).every_thirty_minutes()
schedule.call(task).hourly()
schedule.call(task).hourly_at(17)  # Run at 17 minutes past each hour
schedule.call(task).daily()  # Midnight
schedule.call(task).daily_at("13:00")  # 1pm every day
schedule.call(task).weekly()  # Sunday at midnight
schedule.call(task).weekly_on(1, "09:00")  # Monday at 9am (0=Sunday, 6=Saturday)
schedule.call(task).monthly()  # 1st of month at midnight
schedule.call(task).monthly_on(15, "14:00")  # 15th of month at 2pm
schedule.call(task).yearly()  # January 1st at midnight

# Custom cron expression
schedule.call(task).cron("*/5 * * * *")  # Every 5 minutes
```

### Day Constraints

```python
# Run only on specific days
schedule.call(task).daily().weekdays()  # Monday-Friday
schedule.call(task).daily().weekends()  # Saturday-Sunday
schedule.call(task).daily().mondays()
schedule.call(task).daily().tuesdays()
schedule.call(task).daily().wednesdays()
schedule.call(task).daily().thursdays()
schedule.call(task).daily().fridays()
schedule.call(task).daily().saturdays()
schedule.call(task).daily().sundays()
```

### Conditional Constraints

```python
# Run only when condition is true
def is_production():
    import os
    return os.getenv("FLASK_ENV") == "production"

schedule.call(task).daily().when(is_production)

# Skip when condition is true
def is_maintenance_mode():
    # Check if maintenance mode is enabled
    return False

schedule.call(task).hourly().skip(is_maintenance_mode)
```

## Examples

### Database Cleanup

```python
def cleanup_old_sessions():
    from app import create_app, db
    from datetime import datetime, timedelta
    
    app = create_app()
    with app.app_context():
        # Clean up sessions older than 30 days
        cutoff = datetime.now() - timedelta(days=30)
        # Add your cleanup logic here

schedule.call(cleanup_old_sessions, "Clean old sessions").daily_at("03:00")
```

### Membership Reminders

```python
def send_expiry_reminders():
    from app import create_app
    from app.models import Membership
    from datetime import datetime, timedelta
    
    app = create_app()
    with app.app_context():
        # Find memberships expiring in 30 days
        expiry_date = datetime.now() + timedelta(days=30)
        expiring = Membership.query.filter(
            Membership.end_date <= expiry_date,
            Membership.status == "active"
        ).all()
        
        for membership in expiring:
            # Send reminder email
            pass

schedule.call(send_expiry_reminders, "Membership reminders").weekly_on(1, "09:00")
```

### Weekly Reports

```python
def generate_weekly_stats():
    from app import create_app
    from app.models import User, Shoot
    
    app = create_app()
    with app.app_context():
        # Generate and email weekly statistics
        pass

schedule.call(generate_weekly_stats, "Weekly stats").fridays().daily_at("17:00")
```

### Running Management Commands

```python
# Run existing management commands on a schedule
schedule.command("db backup", "Database backup").daily_at("02:00")
schedule.command("clean", "Clean cache files").weekly()
```

## Troubleshooting

### Check if tasks are defined correctly
```bash
python manage.py schedule list
```

### Manually run tasks to test
```bash
python manage.py schedule run
```

### Common Issues

1. **Tasks not running**: Check cron job is set up correctly with `crontab -l`
2. **Import errors**: Make sure all imports are inside the task function, not at module level
3. **Database access**: Always use Flask app context when accessing the database
4. **Path issues**: Use absolute paths in crontab for both project directory and Python interpreter

### Finding Python Path

```bash
# If using virtual environment
which python

# If using uv
which uv
```

Example crontab with virtual environment:
```bash
* * * * * cd /home/user/SouthEastArchers && /home/user/SouthEastArchers/.venv/bin/python manage.py schedule run >> /var/log/scheduler.log 2>&1
```

Example crontab with uv:
```bash
* * * * * cd /home/user/SouthEastArchers && /home/user/.cargo/bin/uv run python manage.py schedule run >> /var/log/scheduler.log 2>&1
```

## Production Deployment

### Using Docker

Add to your `docker-entrypoint.sh` or create a separate cron container:

```bash
# Install cron in Dockerfile
RUN apt-get update && apt-get install -y cron

# Add crontab entry
RUN echo "* * * * * cd /app && python manage.py schedule run >> /var/log/cron.log 2>&1" | crontab -

# Start cron in entrypoint
service cron start
```

### Using systemd timer (alternative to cron)

Create `/etc/systemd/system/scheduler.service`:
```ini
[Unit]
Description=Run SouthEastArchers scheduled tasks

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/path/to/SouthEastArchers
ExecStart=/path/to/python manage.py schedule run
```

Create `/etc/systemd/system/scheduler.timer`:
```ini
[Unit]
Description=Run scheduler every minute

[Timer]
OnCalendar=*:0/1
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable scheduler.timer
sudo systemctl start scheduler.timer
```

## Comparison to Laravel

| Laravel | This Implementation |
|---------|---------------------|
| `$schedule->call()` | `schedule.call()` |
| `$schedule->command()` | `schedule.command()` |
| `->daily()` | `.daily()` |
| `->dailyAt('13:00')` | `.daily_at("13:00")` |
| `->weekdays()` | `.weekdays()` |
| `->when()` | `.when()` |
| `->skip()` | `.skip()` |
| `php artisan schedule:run` | `python manage.py schedule run` |
| `php artisan schedule:list` | `python manage.py schedule list` |
