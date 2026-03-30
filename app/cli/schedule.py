"""Task scheduler CLI commands."""

import click

schedule_cli = click.Group("schedule", help="Task scheduler commands")


@schedule_cli.command("run")
def schedule_run():
    """Run scheduled tasks that are due"""
    from app.schedule import schedule as scheduler

    click.echo("Running scheduled tasks...")
    scheduler.run_due_tasks()
    click.echo("✓ Scheduled tasks completed")


@schedule_cli.command("list")
def schedule_list():
    """List all scheduled tasks"""
    from app.schedule import schedule as scheduler

    events = scheduler.all_events()

    if not events:
        click.echo("No scheduled tasks defined")
        return

    click.echo("\n{:<40} {:<20}".format("Task", "Schedule"))
    click.echo("-" * 60)

    for event in events:
        click.echo(f"{event.description[:39]:<40} {event.expression:<20}")

    click.echo(f"\nTotal: {len(events)} scheduled tasks")
    click.echo("\nTo run scheduled tasks: flask schedule run")
    click.echo("For production, add to crontab: * * * * * cd /path/to/project && flask schedule run >> /dev/null 2>&1")
