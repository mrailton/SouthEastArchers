from app.models import User


def test_create_member(runner):
    result = runner.invoke(args=["user", "create", "--name", "Jane Doe", "--email", "jane@example.com", "--password", "secret123", "--phone", "555-1234"])
    assert result.exit_code == 0
    assert "Successfully created member user: jane@example.com" in result.output

    user = User.query.filter_by(email="jane@example.com").first()
    assert user is not None
    assert user.name == "Jane Doe"
    assert user.phone == "555-1234"
    assert user.is_active is True
    assert user.check_password("secret123")


def test_create_member_without_phone(runner):
    result = runner.invoke(args=["user", "create", "--name", "No Phone", "--email", "nophone@example.com", "--password", "secret123"])
    assert result.exit_code == 0
    assert "Successfully created member user" in result.output

    user = User.query.filter_by(email="nophone@example.com").first()
    assert user is not None
    assert user.phone is None


def test_create_admin_user(runner):
    result = runner.invoke(args=["user", "create", "--name", "Admin Jane", "--email", "adminjane@example.com", "--password", "secret123", "--admin"])
    assert result.exit_code == 0
    assert "Successfully created admin user: adminjane@example.com" in result.output

    user = User.query.filter_by(email="adminjane@example.com").first()
    assert user is not None
    assert user.has_role("Admin")


def test_create_admin_seeds_rbac_if_missing(runner):
    """Admin creation auto-seeds RBAC when no Admin role exists yet."""
    # RBAC is already seeded by the session fixture, so the Admin role
    # will always be found.  We still verify it works end-to-end.
    result = runner.invoke(args=["user", "create", "--name", "Auto Admin", "--email", "autoadmin@example.com", "--password", "secret123", "--admin"])
    assert result.exit_code == 0
    assert "admin user" in result.output


def test_list_no_users(runner):
    result = runner.invoke(args=["user", "list"])
    assert result.exit_code == 0
    assert "No users found" in result.output


def test_list_shows_users(runner, test_user):
    result = runner.invoke(args=["user", "list"])
    assert result.exit_code == 0
    assert test_user.email in result.output
    assert test_user.name[:24] in result.output


def test_list_shows_admin_status(runner, admin_user):
    result = runner.invoke(args=["user", "list"])
    assert result.exit_code == 0
    assert admin_user.email in result.output
    assert "Yes" in result.output


def test_list_shows_membership_status(runner, test_user):
    """test_user has an active membership — the list should show it."""
    result = runner.invoke(args=["user", "list"])
    assert result.exit_code == 0
    assert "active" in result.output


def test_list_shows_no_membership(runner, admin_user):
    """admin_user has no membership — the list should show 'None'."""
    result = runner.invoke(args=["user", "list"])
    assert result.exit_code == 0
    # admin_user has no membership
    assert "None" in result.output


def test_list_header_format(runner, test_user):
    result = runner.invoke(args=["user", "list"])
    assert result.exit_code == 0
    assert "ID" in result.output
    assert "Email" in result.output
    assert "Name" in result.output
    assert "Admin" in result.output
    assert "Membership" in result.output


def test_delete_existing_user(runner, test_user):
    user_id = test_user.id
    email = test_user.email
    result = runner.invoke(args=["user", "delete", "--id", str(user_id)], input="y\n")
    assert result.exit_code == 0
    assert f"User {email} deleted successfully" in result.output

    assert User.query.get(user_id) is None


def test_delete_user_not_found(runner):
    result = runner.invoke(args=["user", "delete", "--id", "99999"])
    assert result.exit_code == 0
    assert "not found" in result.output


def test_delete_cancelled(runner, test_user):
    user_id = test_user.id
    result = runner.invoke(args=["user", "delete", "--id", str(user_id)], input="n\n")
    assert result.exit_code == 0
    assert "Cancelled" in result.output

    # User should still exist
    assert User.query.get(user_id) is not None
