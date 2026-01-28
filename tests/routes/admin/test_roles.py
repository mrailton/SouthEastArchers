import pytest

from app import db
from app.models import Role


@pytest.fixture()
def role_admin(client, admin_user):
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})
    return client


def test_roles_list(role_admin):
    response = role_admin.get("/admin/roles")
    assert response.status_code == 200
    assert b"Roles" in response.data


def test_create_role(role_admin):
    response = role_admin.post(
        "/admin/roles/create",
        data={
            "name": "test_role",
            "description": "A test role",
            "permissions": [],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Role created successfully" in response.data
    assert Role.query.filter_by(name="test_role").first() is not None


def test_edit_role(role_admin, app):
    with app.app_context():
        role = Role(name="edit_me", description="")
        db.session.add(role)
        db.session.commit()
        rid = role.id

    response = role_admin.post(
        f"/admin/roles/{rid}/edit",
        data={"name": "edited", "description": "Updated", "permissions": []},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Role updated successfully" in response.data
    assert Role.query.filter_by(name="edited").first() is not None


def test_delete_role(role_admin, app):
    with app.app_context():
        role = Role(name="delete_me", description="")
        db.session.add(role)
        db.session.commit()
        rid = role.id

    response = role_admin.post(f"/admin/roles/{rid}/delete", data={}, follow_redirects=True)
    assert response.status_code == 200
    assert Role.query.get(rid) is None
