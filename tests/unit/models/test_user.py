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


def test_has_active_membership_with_active_membership(test_user):
    """Test has_active_membership returns True when user has active membership"""
    assert test_user.has_active_membership


def test_has_active_membership_without_membership(app):
    """Test has_active_membership returns False when user has no membership"""
    from app import db
    from app.models import User

    with app.app_context():
        user = User(name="No Membership", email="nomembership@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        assert not user.has_active_membership


def test_has_active_membership_with_inactive_membership(app):
    """Test has_active_membership returns False when membership is not active"""
    from datetime import date

    from app import db
    from app.models import Membership, User

    with app.app_context():
        user = User(name="Inactive Membership", email="inactivemem@example.com", password_hash="hash")
        db.session.add(user)
        db.session.flush()
        membership = Membership(
            user_id=user.id,
            start_date=date.today(),
            expiry_date=date.today(),
            status="expired",
        )
        db.session.add(membership)
        db.session.commit()

        assert not user.has_active_membership


def test_generate_reset_token(test_user):
    """Test generating password reset token"""
    token = test_user.generate_reset_token()
    assert token is not None
    assert isinstance(token, str)


def test_verify_reset_token_valid(app, test_user):
    """Test verifying valid reset token"""
    from app.services import users

    token = test_user.generate_reset_token()
    verified_user = users.verify_reset_token(token)
    assert verified_user is not None
    assert verified_user.id == test_user.id


def test_verify_reset_token_invalid(app):
    """Test verifying invalid reset token"""
    from app.services import users

    verified_user = users.verify_reset_token("invalid_token")
    assert verified_user is None


def test_verify_reset_token_expired(app, test_user):
    """Test verifying expired reset token"""
    from app.services import users

    verified_user = users.verify_reset_token("invalid_token_string")
    assert verified_user is None

    token = test_user.generate_reset_token()
    verified_user = users.verify_reset_token(token, max_age=3600)
    assert verified_user is not None
    assert verified_user.id == test_user.id
