"""Tests for admin member management"""

from datetime import date, timedelta

from app import db
from app.models import User


def test_members_list(client, admin_user):
    """Test viewing members list"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/members")
    assert response.status_code == 200


def test_member_detail(client, admin_user, test_user):
    """Test viewing member detail"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get(f"/admin/members/{test_user.id}")
    assert response.status_code == 200


def test_create_member_page(client, admin_user):
    """Test accessing create member page"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/members/create")
    assert response.status_code == 200
    assert b"Create Member" in response.data


def test_create_member_success(client, admin_user, app):
    """Test creating a new member"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/members/create",
        data={
            "name": "New Member",
            "email": "newmember@example.com",
            "phone": "1234567890",
            "password": "testpass123",
            "create_membership": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify member was created
    new_user = User.query.filter_by(email="newmember@example.com").first()
    assert new_user is not None
    assert new_user.name == "New Member"
    assert new_user.membership is not None
    assert new_user.membership.initial_credits == 20


def test_create_member_duplicate_email(client, admin_user, test_user):
    """Test creating member with duplicate email"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/members/create",
        data={
            "name": "Duplicate",
            "email": test_user.email,
            "password": "testpass",
        },
    )

    assert response.status_code == 200
    assert b"already registered" in response.data


def test_edit_member_page(client, admin_user, test_user):
    """Test accessing edit member page"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get(f"/admin/members/{test_user.id}/edit")
    assert response.status_code == 200
    assert b"Edit Member" in response.data
    assert test_user.name.encode() in response.data


def test_edit_member_success(client, admin_user, test_user):
    """Test updating member details"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": "Updated Name",
            "email": test_user.email,
            "phone": "9876543210",
            "qualification": test_user.qualification,
            "is_active": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify changes
    db.session.refresh(test_user)
    assert test_user.name == "Updated Name"
    assert test_user.phone == "9876543210"


def test_edit_member_change_password(client, admin_user, test_user):
    """Test changing member password"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": test_user.name,
            "email": test_user.email,
            "qualification": test_user.qualification,
            "password": "newpassword123",
            "is_active": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify password was changed
    db.session.refresh(test_user)
    assert test_user.check_password("newpassword123")


def test_edit_member_membership_dates(client, admin_user, test_user):
    """Test updating membership dates"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    new_start = date.today() - timedelta(days=10)
    new_expiry = date.today() + timedelta(days=355)

    response = client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": test_user.name,
            "email": test_user.email,
            "qualification": test_user.qualification,
            "is_active": "on",
            "membership_start_date": new_start.isoformat(),
            "membership_expiry_date": new_expiry.isoformat(),
            "membership_initial_credits": str(test_user.membership.initial_credits),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify membership dates were updated
    db.session.refresh(test_user)
    assert test_user.membership.start_date == new_start
    assert test_user.membership.expiry_date == new_expiry


def test_edit_member_credits(client, admin_user, test_user):
    """Test updating member credits"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": test_user.name,
            "email": test_user.email,
            "qualification": test_user.qualification,
            "is_active": "on",
            "membership_start_date": test_user.membership.start_date.isoformat(),
            "membership_expiry_date": test_user.membership.expiry_date.isoformat(),
            "membership_initial_credits": "50",
            "membership_purchased_credits": "10",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify credits were updated

    db.session.refresh(test_user)
    assert test_user.membership.initial_credits == 50
    assert test_user.membership.purchased_credits == 10


def test_edit_member_without_membership(client, admin_user, app):
    """Test editing member without membership"""
    user = User(
        name="No Membership User",
        email="nomembership@example.com",
        qualification="none",
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        f"/admin/members/{user.id}/edit",
        data={
            "name": "Updated Name",
            "email": user.email,
            "qualification": "beginner",
            "is_active": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify name was updated even without membership
    db.session.refresh(user)
    assert user.name == "Updated Name"


def test_members_requires_admin(client, test_user):
    """Test that members list requires admin"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/members")
    assert response.status_code in [302, 403]


def test_member_detail_not_found(client, admin_user):
    """Test viewing non-existent member"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/members/99999")
    assert response.status_code == 404


def test_renew_membership(client, admin_user, test_user, app):
    """Test renewing a member's membership"""

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Use canonical membership renew endpoint
    response = client.post(
        f"/admin/members/{test_user.id}/membership/renew",
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_renew_membership_nonexistent(client, admin_user):
    """Test renewing a non-existent member returns 404"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post("/admin/members/99999/membership/renew")
    assert response.status_code == 404


def test_deactivate_member(client, admin_user, test_user):
    """Test deactivating a member via admin"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Deactivate via the edit endpoint by clearing the is_active flag
    response = client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": test_user.name,
            "email": test_user.email,
            "is_active": "",  # unchecked
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_activate_member(client, admin_user, test_user):
    """Test activating a member via admin"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Activate via the edit endpoint by setting is_active
    response = client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": test_user.name,
            "email": test_user.email,
            "is_active": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_activate_user_success(client, admin_user, test_user, mocker):
    """Test activating inactive user sends welcome email"""
    mock_send_email = mocker.patch("app.services.mail_service.send_welcome_email")

    # Make test user inactive
    test_user.is_active = False
    from app import db

    db.session.commit()

    # Login as admin
    with client:
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"}, follow_redirects=True)

        response = client.post(f"/admin/members/{test_user.id}/activate", follow_redirects=True)

        assert response.status_code == 200
        assert b"Account activated" in response.data
        assert b"Welcome email sent" in response.data

        # Verify user is now active
        from app.models import User

        user = db.session.get(User, test_user.id)
        assert user.is_active is True

        # Verify email was sent
        mock_send_email.assert_called_once_with(test_user.id)


def test_activate_user_already_active(client, admin_user, test_user):
    """Test activating already active user shows warning"""
    # Ensure test user is active
    test_user.is_active = True
    from app import db

    db.session.commit()

    # Login as admin
    with client:
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"}, follow_redirects=True)

        response = client.post(f"/admin/members/{test_user.id}/activate", follow_redirects=True)

        assert response.status_code == 200
        assert b"already active" in response.data


def test_activate_user_not_found(client, admin_user):
    """Test activating non-existent user returns 404"""
    # Login as admin
    with client:
        client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"}, follow_redirects=True)

        response = client.post("/admin/members/99999/activate", follow_redirects=False)

        assert response.status_code == 404
