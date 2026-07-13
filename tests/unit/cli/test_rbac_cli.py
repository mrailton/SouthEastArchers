from app.cli import cli
from app.models import Permission, Role


def test_seed_creates_roles_and_permissions(runner):
    result = runner.invoke(cli, ["rbac", "seed"])
    assert result.exit_code == 0
    assert "RBAC roles and permissions seeded" in result.output

    assert Role.query.filter_by(name="Admin").first() is not None
    assert Role.query.filter_by(name="Membership Manager").first() is not None
    assert Role.query.filter_by(name="Content Manager").first() is not None
    assert len(Permission.query.all()) > 0


def test_seed_is_idempotent(runner):
    runner.invoke(cli, ["rbac", "seed"])
    role_count_after_first = Role.query.count()
    perm_count_after_first = Permission.query.count()

    result = runner.invoke(cli, ["rbac", "seed"])
    assert result.exit_code == 0
    assert Role.query.count() == role_count_after_first
    assert Permission.query.count() == perm_count_after_first
