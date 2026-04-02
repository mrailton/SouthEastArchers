from app.models import Permission, Role


def test_seed_creates_roles_and_permissions(runner):
    """RBAC seed should create roles and permissions."""
    result = runner.invoke(args=["rbac", "seed"])
    assert result.exit_code == 0
    assert "RBAC roles and permissions seeded" in result.output

    # Verify roles were created
    admin_role = Role.query.filter_by(name="Admin").first()
    assert admin_role is not None

    membership_manager = Role.query.filter_by(name="Membership Manager").first()
    assert membership_manager is not None

    content_manager = Role.query.filter_by(name="Content Manager").first()
    assert content_manager is not None

    # Verify permissions were created
    permissions = Permission.query.all()
    assert len(permissions) > 0


def test_seed_is_idempotent(runner):
    """Running seed twice should not create duplicates."""
    runner.invoke(args=["rbac", "seed"])
    role_count_after_first = Role.query.count()
    perm_count_after_first = Permission.query.count()

    result = runner.invoke(args=["rbac", "seed"])
    assert result.exit_code == 0

    assert Role.query.count() == role_count_after_first
    assert Permission.query.count() == perm_count_after_first
