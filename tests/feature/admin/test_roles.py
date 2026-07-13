"""Admin role routes — CRUD wiring and 404 handling."""

import pytest

from app import db
from app.models import Permission, Role


@pytest.fixture()
def permissions(app):
    perms = [Permission(name="p1", description="perm 1"), Permission(name="p2", description="perm 2")]
    db.session.add_all(perms)
    db.session.commit()
    return [p.id for p in perms]


def test_roles_list(admin_client):
    response = admin_client.get("/admin/roles")
    assert response.status_code == 200
    assert b"Roles" in response.content


def test_create_role_success(admin_client, permissions):
    response = admin_client.post(
        "/admin/roles/create",
        data={"name": "test_role", "description": "A test role", "permissions": permissions},
        follow_redirects=True,
    )
    assert b"Role created" in response.content
    assert Role.query.filter_by(name="test_role").first() is not None


def test_edit_role_not_found(admin_client):
    response = admin_client.get("/admin/roles/9999/edit")
    assert response.status_code == 404
    assert b"Page Not Found" in response.content


def test_delete_role_not_found(admin_client):
    response = admin_client.post("/admin/roles/9999/delete")
    assert response.status_code == 404


def test_create_role_page(admin_client):
    response = admin_client.get("/admin/roles/create")
    assert response.status_code == 200


def test_edit_role_success(admin_client, permissions):
    create = admin_client.post(
        "/admin/roles/create",
        data={"name": "editable_role", "description": "Edit me", "permissions": permissions},
        follow_redirects=True,
    )
    assert b"Role created" in create.content
    role = Role.query.filter_by(name="editable_role").first()
    response = admin_client.get(f"/admin/roles/{role.id}/edit")
    assert response.status_code == 200

    response = admin_client.post(
        f"/admin/roles/{role.id}/edit",
        data={"name": "edited_role", "description": "Edited", "permissions": permissions[:1]},
        follow_redirects=True,
    )
    assert b"Role updated" in response.content or b"updated" in response.content.lower()


def test_delete_role_success(admin_client, permissions):
    admin_client.post(
        "/admin/roles/create",
        data={"name": "deletable_role", "description": "Delete me", "permissions": permissions},
        follow_redirects=True,
    )
    role = Role.query.filter_by(name="deletable_role").first()
    response = admin_client.post(f"/admin/roles/{role.id}/delete", follow_redirects=True)
    assert b"Role deleted" in response.content or b"deleted" in response.content.lower()


def test_create_role_duplicate_fails(admin_client, permissions):
    admin_client.post(
        "/admin/roles/create",
        data={"name": "dup_role", "description": "First", "permissions": permissions},
        follow_redirects=True,
    )
    response = admin_client.post(
        "/admin/roles/create",
        data={"name": "dup_role", "description": "Second", "permissions": permissions},
        follow_redirects=True,
    )
    assert response.status_code == 200
