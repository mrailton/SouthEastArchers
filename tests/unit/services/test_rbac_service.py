from unittest.mock import patch

from app import db
from app.models import Permission, Role
from app.services import rbac


def test_list_roles(app):
    with app.app_context():
        r1 = Role(name="A")
        r2 = Role(name="B")
        db.session.add_all([r1, r2])
        db.session.commit()

        roles = rbac.list_roles()
        assert len(roles) >= 2
        names = [r.name for r in roles]
        assert "A" in names
        assert "B" in names


def test_list_permissions(app):
    with app.app_context():
        p1 = Permission(name="P1")
        p2 = Permission(name="P2")
        db.session.add_all([p1, p2])
        db.session.commit()

        perms = rbac.list_permissions()
        assert len(perms) >= 2
        names = [p.name for p in perms]
        assert "P1" in names
        assert "P2" in names


def test_create_role_duplicate(app):
    with app.app_context():
        Role.query.filter_by(name="duplicate").delete()
        rbac.create_role("duplicate", "desc", [])
        result = rbac.create_role("duplicate", "desc", [])
        assert result.data is None
        assert "already exists" in result.message


def test_create_role_exception(app):
    with app.app_context():
        with patch("app.repositories.base.db.session.add", side_effect=Exception("DB Error")):
            result = rbac.create_role("exception_role", "desc", [])
            assert result.data is None
            assert "Error creating role" in result.message


def test_update_role_duplicate(app):
    with app.app_context():
        r1 = Role(name="r1")
        r2 = Role(name="r2")
        db.session.add_all([r1, r2])
        db.session.commit()

        result = rbac.update_role(r1, "r2", "desc", [])
        assert not result.success
        assert "already exists" in result.message


def test_update_role_exception(app):
    with app.app_context():
        role = Role(name="upd_exc")
        db.session.add(role)
        db.session.commit()

        with patch("app.repositories.base.db.session.commit", side_effect=Exception("DB Error")):
            result = rbac.update_role(role, "new_name", "desc", [])
            assert not result.success
            assert "Error updating role" in result.message


def test_delete_role_exception(app):
    with app.app_context():
        role = Role(name="del_exc")
        db.session.add(role)
        db.session.commit()

        with patch("app.repositories.base.db.session.commit", side_effect=Exception("DB Error")):
            result = rbac.delete_role(role)
            assert not result.success
            assert "Error deleting role" in result.message
