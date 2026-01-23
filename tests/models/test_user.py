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
