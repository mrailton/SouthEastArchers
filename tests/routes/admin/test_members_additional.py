from unittest.mock import MagicMock, patch

from app import db
from app.models import Payment, User


def test_activate_membership_not_found(client, admin_user):
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post("/admin/members/99999/membership/activate")
    assert response.status_code == 404


def test_activate_membership_service_failure(client, admin_user, test_user):
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Patch MembershipService.activate_membership to return failure
    with patch("app.routes.admin.members.MembershipService.activate_membership", return_value=(False, "Error reason")):
        response = client.post(f"/admin/members/{test_user.id}/membership/activate", follow_redirects=True)
        assert response.status_code == 200
        assert b"Error reason" in response.data


def test_activate_membership_with_payment_sends_receipt(client, admin_user, test_user):
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create a completed payment for the test user
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    with patch("app.routes.admin.members.MembershipService.activate_membership", return_value=(True, "Activated")):
        with patch("app.routes.admin.members.send_payment_receipt") as mock_send:
            response = client.post(f"/admin/members/{test_user.id}/membership/activate", follow_redirects=True)
            assert response.status_code == 200
            mock_send.assert_called_once()
            assert b"Receipt email sent" in response.data


def test_activate_membership_with_payment_send_failure(client, admin_user, test_user):
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="completed",
    )
    db.session.add(payment)
    db.session.commit()

    with patch("app.routes.admin.members.MembershipService.activate_membership", return_value=(True, "Activated")):
        with patch("app.routes.admin.members.send_payment_receipt", side_effect=Exception("Email fail")):
            response = client.post(f"/admin/members/{test_user.id}/membership/activate", follow_redirects=True)
            assert response.status_code == 200
            assert b"Email failed to send" in response.data


def test_create_member_service_error_shows_message(client, admin_user):
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    with patch("app.routes.admin.members.UserService.create_member", return_value=(None, "already registered")):
        response = client.post(
            "/admin/members/create",
            data={
                "name": "Duplicate",
                "email": "dup@example.com",
                "password": "test",
            },
        )
        assert response.status_code == 200
        assert b"already registered" in response.data


def test_edit_member_not_found(client, admin_user):
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post("/admin/members/99999/edit")
    assert response.status_code == 404


def test_edit_member_flashes_validation_errors(client, admin_user, test_user):
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Post invalid data (empty name) to trigger form.errors flash
    response = client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": "",  # invalid
            "email": test_user.email,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    # WTForms should flash an error about required/length
    assert b"This field is required" in response.data or b"Field must be at least" in response.data
