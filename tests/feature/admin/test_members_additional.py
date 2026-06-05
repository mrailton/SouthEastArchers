"""Admin member route edge cases not covered elsewhere."""

from unittest.mock import patch

from app.services.result import ServiceResult


def test_activate_membership_not_found(admin_client):
    response = admin_client.post("/admin/members/99999/membership/activate")
    assert response.status_code == 404


def test_activate_membership_service_failure_shows_flash(admin_client, test_user):
    with patch(
        "app.routes.admin.members.memberships.activate_membership",
        return_value=ServiceResult.fail("Error reason"),
    ):
        response = admin_client.post(
            f"/admin/members/{test_user.id}/membership/activate",
            follow_redirects=True,
        )
    assert b"Error reason" in response.content


def test_edit_member_not_found(admin_client):
    response = admin_client.post("/admin/members/99999/edit")
    assert response.status_code == 404


def test_renew_membership(admin_client, test_user):
    response = admin_client.post(
        f"/admin/members/{test_user.id}/membership/renew",
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_create_membership_for_user_without_one(admin_client, app):
    from app import db
    from app.models import User

    user = User(name="No Membership", email="nomembership@example.com", phone="1", is_active=True)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    response = admin_client.post(
        f"/admin/members/{user.id}/membership/create",
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_activate_membership_with_completed_payment(admin_client, test_user):
    from tests.helpers import create_payment_for_user
    from app import db

    test_user.membership.status = "pending"
    db.session.commit()
    create_payment_for_user(
        db,
        user=test_user,
        payment_type="membership",
        status="completed",
    )
    response = admin_client.post(
        f"/admin/members/{test_user.id}/membership/activate",
        follow_redirects=True,
    )
    assert b"activated" in response.content.lower()


def test_adjust_credits_no_membership(admin_client, app):
    from app import db
    from app.models import User

    user = User(name="No Mem", email="nocredits@example.com", phone="1", is_active=True)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    response = admin_client.post(
        f"/admin/members/{user.id}/credits/adjust",
        data={"quantity": "1", "action": "add"},
        follow_redirects=True,
    )
    assert b"does not have a membership" in response.content


def test_adjust_credits_invalid_quantity(admin_client, test_user):
    response = admin_client.post(
        f"/admin/members/{test_user.id}/credits/adjust",
        data={"quantity": "not-a-number", "action": "add"},
        follow_redirects=True,
    )
    assert b"valid number" in response.content
