import pytest

from app.dependencies import LoginRequired
from app.exceptions import AuthorizationError
from app.policies import has_any_permission, has_permission, require_all_permissions, require_permission


def test_has_permission_none_user():
    assert has_permission(None, "members.read") is False


def test_has_permission_with_permission(admin_user):
    assert has_permission(admin_user, "members.read") is True


def test_has_any_permission_empty_list(admin_user):
    assert has_any_permission(admin_user) is False


def test_require_permission_empty_names_allows(admin_user):
    require_permission(admin_user)


def test_has_any_permission_none_user():
    assert has_any_permission(None, "members.read") is False


def test_require_permission_raises_login_required():
    with pytest.raises(LoginRequired):
        require_permission(None, "members.read")


def test_require_permission_raises_authorization_error(member_client, test_user):
    with pytest.raises(AuthorizationError):
        require_permission(test_user, "roles.manage")


def test_require_all_permissions_missing_one(app):
    from app import db
    from tests.helpers import create_user_with_permissions

    user = create_user_with_permissions(db, ["finance.read"])
    with pytest.raises(AuthorizationError, match="finance.delete"):
        require_all_permissions(user, "finance.read", "finance.delete")


def test_require_all_permissions_success(admin_user):
    require_all_permissions(admin_user, "members.read", "finance.read")
