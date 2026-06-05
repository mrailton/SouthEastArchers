"""Admin member routes — HTTP wiring, permissions, and flashes (business logic: users service tests)."""

from app import db
from app.models import User


def test_members_list(admin_client):
    response = admin_client.get("/admin/members")
    assert response.status_code == 200


def test_member_detail(admin_client, test_user):
    response = admin_client.get(f"/admin/members/{test_user.id}")
    assert response.status_code == 200


def test_create_member_page(admin_client):
    response = admin_client.get("/admin/members/create")
    assert response.status_code == 200
    assert b"Create Member" in response.content


def test_create_member_success_redirects(admin_client):
    response = admin_client.post(
        "/admin/members/create",
        data={
            "name": "New Member",
            "email": "newmember@example.com",
            "phone": "1234567890",
            "password": "testpass123",
            "create_membership": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert User.query.filter_by(email="newmember@example.com").first() is not None


def test_create_member_duplicate_email_shows_error(admin_client, test_user):
    response = admin_client.post(
        "/admin/members/create",
        data={"name": "Duplicate", "email": test_user.email, "password": "testpass"},
    )
    assert response.status_code in (200, 422)
    assert b"already registered" in response.content


def test_edit_member_page(admin_client, test_user):
    response = admin_client.get(f"/admin/members/{test_user.id}/edit")
    assert response.status_code == 200
    assert b"Edit Member" in response.content


def test_edit_member_success_flash(admin_client, test_user):
    response = admin_client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": "Updated Name",
            "email": test_user.email,
            "qualification": test_user.qualification,
            "is_active": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_add_credits_success_flash(admin_client, test_user):
    response = admin_client.post(
        f"/admin/members/{test_user.id}/credits/adjust",
        data={"quantity": "5", "reason": "Promotional credits", "action": "add"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Added 5 credit(s)" in response.content


def test_add_credits_requires_permission(member_client, test_user):
    response = member_client.post(
        f"/admin/members/{test_user.id}/credits/adjust",
        data={"quantity": "5", "action": "add"},
    )
    assert response.status_code == 403


def test_members_requires_admin(member_client):
    response = member_client.get("/admin/members")
    assert response.status_code in (302, 403)


def test_member_detail_not_found(admin_client):
    response = admin_client.get("/admin/members/99999")
    assert response.status_code == 404


def test_activate_user_success_flash(admin_client, test_user, mocker):
    mocker.patch("app.services.mail.send_welcome_email")
    test_user.is_active = False
    db.session.commit()

    response = admin_client.post(f"/admin/members/{test_user.id}/activate", follow_redirects=True)
    assert response.status_code == 200
    assert b"Account activated" in response.content


def test_activate_user_not_found(admin_client):
    response = admin_client.post("/admin/members/99999/activate", follow_redirects=False)
    assert response.status_code == 404
