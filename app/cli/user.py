"""User management CLI commands."""

import click
from flask.cli import AppGroup

from app import db

user_cli = AppGroup("user", help="User management commands")


@user_cli.command("create")
@click.option("--name", prompt="Full name", help="User full name")
@click.option("--email", prompt="Email", help="User email")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="User password",
)
@click.option("--phone", default="", help="Phone number (optional)")
@click.option("--admin", is_flag=True, help="Create as admin user")
def user_create(name, email, password, phone, admin):
    """Create a new user"""
    from app.models import User
    from app.models.rbac import Role, seed_rbac

    user = User(
        name=name,
        email=email,
        phone=phone if phone else None,
        is_active=True,
    )
    user.set_password(password)

    if admin:
        admin_role = Role.query.filter_by(name="Admin").first()
        if not admin_role:
            seed_rbac(db.session)
            admin_role = Role.query.filter_by(name="Admin").first()
        if admin_role:
            user.roles.append(admin_role)

    db.session.add(user)
    db.session.flush()
    db.session.commit()

    user_type = "admin" if admin else "member"
    click.echo(f"✓ Successfully created {user_type} user: {email}")


@user_cli.command("list")
def user_list():
    """List all users"""
    from app.models import User

    users = User.query.all()

    if not users:
        click.echo("No users found")
        return

    click.echo("\n{:<5} {:<30} {:<25} {:<10} {:<12}".format("ID", "Email", "Name", "Admin", "Membership"))
    click.echo("-" * 90)

    for user in users:
        admin_status = "Yes" if any(r.name == "Admin" for r in user.roles) else "No"
        membership = user.membership
        membership_status = membership.status if membership else "None"
        click.echo(f"{user.id:<5} {user.email:<30} {user.name[:24]:<25} {admin_status:<10} {membership_status:<12}")


@user_cli.command("delete")
@click.option("--id", "user_id", prompt="User ID", type=int, help="User ID to delete")
def user_delete(user_id):
    """Delete a user"""
    from app.models import User

    user = User.query.get(user_id)

    if not user:
        click.echo(f"Error: User with ID {user_id} not found")
        return

    if click.confirm(f"Are you sure you want to delete {user.email}?"):
        db.session.delete(user)
        db.session.commit()
        click.echo(f"✓ User {user.email} deleted successfully")
    else:
        click.echo("Cancelled")
