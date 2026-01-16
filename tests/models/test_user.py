"""Tests for user model"""


def test_password_hashing(test_user):
    assert not test_user.password_hash == "password123"
    assert test_user.check_password("password123")
    assert not test_user.check_password("wrongpassword")
