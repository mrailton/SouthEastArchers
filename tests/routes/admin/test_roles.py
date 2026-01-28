import pytest

from app import db
from app.models import Permission, Role


@pytest.fixture()
def permissions(app):
    with app.app_context():
        p1 = Permission(name="p1", description="perm 1")
        p2 = Permission(name="p2", description="perm 2")
        db.session.add_all([p1, p2])
        db.session.commit()
        return [p1.id, p2.id]


@pytest.fixture()
def role_admin(client, admin_user):
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})
    return client


def test_roles_list(role_admin):
    response = role_admin.get("/admin/roles")
    assert response.status_code == 200
    assert b"Roles" in response.data


def test_create_role_get(role_admin):
    response = role_admin.get("/admin/roles/create")
    assert response.status_code == 200
    assert b"Create Role" in response.data


def test_create_role(role_admin, permissions):
    response = role_admin.post(
        "/admin/roles/create",
        data={
            "name": "test_role",
            "description": "A test role",
            "permissions": permissions,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Role created successfully" in response.data
    role = Role.query.filter_by(name="test_role").first()
    assert role is not None
    assert len(role.permissions) == 2


def test_create_role_duplicate(role_admin):
    role_admin.post(
        "/admin/roles/create",
        data={"name": "dup", "description": "", "permissions": []},
    )
    response = role_admin.post(
        "/admin/roles/create",
        data={"name": "dup", "description": "", "permissions": []},
        follow_redirects=True,
    )
    assert b"Role name already exists" in response.data


def test_create_role_invalid_form(role_admin):
    response = role_admin.post(
        "/admin/roles/create",
        data={"name": "", "description": "", "permissions": []},
        follow_redirects=True,
    )
    assert b"This field is required" in response.data


def test_edit_role_get(role_admin, app):
    with app.app_context():
        role = Role(name="edit_get", description="")
        db.session.add(role)
        db.session.commit()
        rid = role.id

    response = role_admin.get(f"/admin/roles/{rid}/edit")
    assert response.status_code == 200
    assert b"Edit Role" in response.data


def test_edit_role_not_found(role_admin):
    response = role_admin.get("/admin/roles/9999/edit", follow_redirects=True)
    assert b"Role not found" in response.data
    response = role_admin.post("/admin/roles/9999/edit", data={}, follow_redirects=True)
    assert b"Role not found" in response.data


def test_edit_role(role_admin, app, permissions):
    with app.app_context():
        role = Role(name="edit_me", description="")
        db.session.add(role)
        db.session.commit()
        rid = role.id

    response = role_admin.post(
        f"/admin/roles/{rid}/edit",
        data={
            "name": "edited",
            "description": "Updated",
            "permissions": [permissions[0]],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Role updated successfully" in response.data
    role = Role.query.get(rid)
    assert role.name == "edited"
    assert len(role.permissions) == 1


def test_edit_role_duplicate_name(role_admin, app):
    with app.app_context():
        r1 = Role(name="r1", description="")
        r2 = Role(name="r2", description="")
        db.session.add_all([r1, r2])
        db.session.commit()
        r2_id = r2.id

    response = role_admin.post(
        f"/admin/roles/{r2_id}/edit",
        data={"name": "r1", "description": "", "permissions": []},
        follow_redirects=True,
    )
    assert b"Role name already exists" in response.data


def test_edit_role_invalid_form(role_admin, app):
    with app.app_context():
        role = Role(name="edit_inv", description="")
        db.session.add(role)
        db.session.commit()
        rid = role.id

    response = role_admin.post(
        f"/admin/roles/{rid}/edit",
        data={"name": "", "description": "", "permissions": []},
        follow_redirects=True,
    )
    assert b"This field is required" in response.data


def test_delete_role(role_admin, app):
    with app.app_context():
        role = Role(name="delete_me", description="")
        db.session.add(role)
        db.session.commit()
        rid = role.id

    response = role_admin.post(f"/admin/roles/{rid}/delete", data={}, follow_redirects=True)
    assert response.status_code == 200
    assert Role.query.get(rid) is None


def test_delete_role_not_found(role_admin):
    response = role_admin.post("/admin/roles/9999/delete", follow_redirects=True)
    assert b"Role not found" in response.data
