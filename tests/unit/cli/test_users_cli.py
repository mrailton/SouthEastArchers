from unittest.mock import patch

from app.cli import cli
from app.models import Role, User


def _input(*lines: str) -> str:
    """Join interactive prompt responses with newlines."""
    return "\n".join(lines) + "\n"


def _create_input(
    name: str = "Test Archer",
    email: str = "archer@example.com",
    password: str = "secret123",
    phone: str = "",
    role_ids: str = "",
    activate: str = "n",
    membership: str = "n",
) -> str:
    return _input(name, email, password, password, phone, role_ids, activate, membership)


class TestUsersCreateBasic:
    def test_creates_user_with_minimal_input(self, runner, app):
        result = runner.invoke(cli, ["users", "create"], input=_create_input())

        assert result.exit_code == 0
        assert "✓ User 'Test Archer' (archer@example.com) created successfully." in result.output
        assert User.query.filter_by(email="archer@example.com").first() is not None

    def test_creates_user_with_phone(self, runner, app):
        result = runner.invoke(
            cli,
            ["users", "create"],
            input=_create_input(phone="07700900000"),
        )

        assert result.exit_code == 0
        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        assert user.phone == "07700900000"

    def test_new_user_is_inactive_by_default(self, runner, app):
        runner.invoke(cli, ["users", "create"], input=_create_input())

        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        assert user.is_active is False

    def test_no_roles_assigned_when_blank_input(self, runner, app):
        runner.invoke(cli, ["users", "create"], input=_create_input(role_ids=""))

        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        assert user.roles == []

    def test_fails_on_duplicate_email(self, runner, app, test_user):
        result = runner.invoke(
            cli,
            ["users", "create"],
            input=_create_input(email=test_user.email),
        )

        assert result.exit_code == 1
        assert "✗" in result.output


class TestUsersCreateWithRoles:
    def test_assigns_role_by_id(self, runner, app):
        admin_role = Role.query.filter_by(name="Admin").first()
        assert admin_role is not None

        result = runner.invoke(
            cli,
            ["users", "create"],
            input=_create_input(role_ids=str(admin_role.id)),
        )

        assert result.exit_code == 0
        assert "Admin" in result.output
        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        assert any(r.name == "Admin" for r in user.roles)

    def test_assigns_multiple_roles(self, runner, app):
        admin_role = Role.query.filter_by(name="Admin").first()
        content_role = Role.query.filter_by(name="Content Manager").first()
        assert admin_role and content_role

        result = runner.invoke(
            cli,
            ["users", "create"],
            input=_create_input(role_ids=f"{admin_role.id},{content_role.id}"),
        )

        assert result.exit_code == 0
        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        role_names = {r.name for r in user.roles}
        assert "Admin" in role_names
        assert "Content Manager" in role_names

    def test_skips_unknown_role_ids(self, runner, app):
        result = runner.invoke(
            cli,
            ["users", "create"],
            input=_create_input(role_ids="9999"),
        )

        assert result.exit_code == 0
        assert "Skipping unknown role ID" in result.output
        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        assert user.roles == []

    def test_skips_invalid_non_numeric_role_ids(self, runner, app):
        result = runner.invoke(
            cli,
            ["users", "create"],
            input=_create_input(role_ids="abc"),
        )

        assert result.exit_code == 0
        assert "Skipping unknown role ID" in result.output
        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        assert user.roles == []


class TestUsersCreateActivation:
    @patch("app.events.payloads.emit_user_activated", return_value=None)
    def test_activates_account_when_confirmed(self, _mock_emit, runner, app):
        result = runner.invoke(
            cli,
            ["users", "create"],
            input=_create_input(activate="y"),
        )

        assert result.exit_code == 0
        assert "Account: active" in result.output
        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        assert user.is_active is True

    def test_does_not_activate_when_declined(self, runner, app):
        result = runner.invoke(
            cli,
            ["users", "create"],
            input=_create_input(activate="n"),
        )

        assert result.exit_code == 0
        assert "Account: active" not in result.output
        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        assert user.is_active is False


class TestUsersCreateMembership:
    @patch("app.services.settings.get", return_value=10)
    @patch("app.services.settings.calculate_membership_expiry")
    def test_creates_membership_when_confirmed(self, mock_expiry, _mock_get, runner, app):
        from datetime import datetime, timedelta

        mock_expiry.return_value = datetime.today() + timedelta(days=365)

        result = runner.invoke(
            cli,
            ["users", "create"],
            input=_create_input(membership="y"),
        )

        assert result.exit_code == 0
        assert "Membership: created" in result.output
        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        assert user.membership is not None

    def test_does_not_create_membership_when_declined(self, runner, app):
        result = runner.invoke(
            cli,
            ["users", "create"],
            input=_create_input(membership="n"),
        )

        assert result.exit_code == 0
        assert "Membership: created" not in result.output
        user = User.query.filter_by(email="archer@example.com").first()
        assert user is not None
        assert user.membership is None


class TestUsersCreateServiceFailure:
    def test_exits_nonzero_on_service_failure(self, runner, app):
        from app.services.result import ServiceResult

        with patch("app.services.users.create_member", return_value=ServiceResult.fail("Something went wrong")):
            result = runner.invoke(
                cli,
                ["users", "create"],
                input=_create_input(),
            )

        assert result.exit_code == 1
        assert "✗ Something went wrong" in result.output
