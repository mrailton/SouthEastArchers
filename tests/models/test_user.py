"""Tests for user model"""


def test_password_hashing(test_user):
    assert not test_user.password_hash == "password123"
    assert test_user.check_password("password123")
    assert not test_user.check_password("wrongpassword")


def test_user_repr(test_user):
    """Test user __repr__ method"""
    repr_str = repr(test_user)
    assert f"<User {test_user.email}>" == repr_str
    assert "test@example.com" in repr_str


def test_user_rbac_helpers(app):
    from app import db
    from app.models import Permission, Role, User

    with app.app_context():
        p1 = Permission(name="p1")
        p2 = Permission(name="p2")
        r1 = Role(name="r1", permissions=[p1])
        r2 = Role(name="r2", permissions=[p2])
        user = User(name="Test", email="test_rbac@example.com", password_hash="hash")
        db.session.add_all([p1, p2, r1, r2, user])
        db.session.commit()

        assert not user.has_role("r1")
        assert not user.has_permission("p1")
        assert not user.has_any_permission("p1", "p2")
        assert not user.has_any_permission()

        user.roles.append(r1)
        db.session.commit()

        assert user.has_role("r1")
        assert not user.has_role("r2")
        assert user.has_permission("p1")
        assert not user.has_permission("p2")
        assert user.has_any_permission("p1")
        assert user.has_any_permission("p1", "p2")
        assert not user.has_any_permission("p2")

        user.roles.append(r2)
        db.session.commit()
        assert user.has_any_permission("p2")
