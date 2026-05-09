"""Tests for admin member management"""

from datetime import date, timedelta

from app import db
from app.models import User


def test_members_list(admin_client):
    """Test viewing members list"""
    response = admin_client.get("/admin/members")
    assert response.status_code == 200


def test_member_detail(admin_client, test_user):
    """Test viewing member detail"""
    response = admin_client.get(f"/admin/members/{test_user.id}")
    assert response.status_code == 200


def test_create_member_page(admin_client):
    """Test accessing create member page"""
    response = admin_client.get("/admin/members/create")
    assert response.status_code == 200
    assert b"Create Member" in response.data


def test_create_member_success(admin_client, app):
    """Test creating a new member"""
    response = admin_client.post(
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

    new_user = User.query.filter_by(email="newmember@example.com").first()
    assert new_user is not None
    assert new_user.name == "New Member"
    assert new_user.membership is not None
    assert new_user.membership.initial_credits == 20


def test_create_member_duplicate_email(admin_client, test_user):
    """Test creating member with duplicate email"""
    response = admin_client.post(
        "/admin/members/create",
        data={
            "name": "Duplicate",
            "email": test_user.email,
            "password": "testpass",
        },
    )

    assert response.status_code == 200
    assert b"already registered" in response.data


def test_edit_member_page(admin_client, test_user):
    """Test accessing edit member page"""
    response = admin_client.get(f"/admin/members/{test_user.id}/edit")
    assert response.status_code == 200
    assert b"Edit Member" in response.data
    assert test_user.name.encode() in response.data


def test_edit_member_success(admin_client, test_user):
    """Test updating member details"""
    response = admin_client.post(
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

    db.session.refresh(test_user)
    assert test_user.name == "Updated Name"
    assert test_user.phone == "9876543210"


def test_edit_member_change_password(admin_client, test_user):
    """Test changing member password"""
    response = admin_client.post(
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

    db.session.refresh(test_user)
    assert test_user.check_password("newpassword123")


def test_edit_member_membership_dates(admin_client, test_user):
    """Test updating membership dates"""
    new_start = date.today() - timedelta(days=10)
    new_expiry = date.today() + timedelta(days=355)

    response = admin_client.post(
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


def test_edit_member_credits(admin_client, test_user):
    """Test updating member credits"""
    response = admin_client.post(
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

    db.session.refresh(test_user)
    assert test_user.membership.initial_credits == 50
    assert test_user.membership.purchased_credits == 10


def test_edit_member_without_membership(admin_client, app):
    """Test editing member without membership"""
    user = User(
        name="No Membership User",
        email="nomembership@example.com",
        qualification="none",
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    response = admin_client.post(
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

    db.session.refresh(user)
    assert user.name == "Updated Name"


def test_add_credits_success(admin_client, test_user):
    """Test adding credits to a member's account"""
    initial_credits = test_user.membership.purchased_credits

    response = admin_client.post(
        f"/admin/members/{test_user.id}/credits/adjust",
        data={
            "quantity": "5",
            "reason": "Promotional credits",
            "action": "add",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Added 5 credit(s)" in response.data

    db.session.refresh(test_user)
    assert test_user.membership.purchased_credits == initial_credits + 5


def test_add_credits_creates_credit_record(admin_client, test_user):
    """Test that adding credits creates a Credit record"""
    from app.models import Credit

    initial_count = Credit.query.filter_by(user_id=test_user.id).count()

    admin_client.post(
        f"/admin/members/{test_user.id}/credits/adjust",
        data={"quantity": "3", "action": "add"},
        follow_redirects=True,
    )

    credits = Credit.query.filter_by(user_id=test_user.id).all()
    assert len(credits) == initial_count + 1
    assert credits[-1].amount == 3
    assert credits[-1].payment_id is None


def test_remove_credits_success(admin_client, test_user):
    """Test removing credits from a member's account (initial credits first)"""
    test_user.membership.initial_credits = 10
    test_user.membership.purchased_credits = 5
    db.session.commit()

    response = admin_client.post(
        f"/admin/members/{test_user.id}/credits/adjust",
        data={
            "quantity": "4",
            "reason": "Correction",
            "action": "remove",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Removed 4 credit(s)" in response.data

    db.session.refresh(test_user)
    assert test_user.membership.initial_credits == 6
    assert test_user.membership.purchased_credits == 5


def test_remove_credits_spills_into_purchased(admin_client, test_user):
    """Test removing more credits than initial spills into purchased credits"""
    test_user.membership.initial_credits = 3
    test_user.membership.purchased_credits = 10
    db.session.commit()

    admin_client.post(
        f"/admin/members/{test_user.id}/credits/adjust",
        data={"quantity": "5", "action": "remove"},
        follow_redirects=True,
    )

    db.session.refresh(test_user)
    assert test_user.membership.initial_credits == 0
    assert test_user.membership.purchased_credits == 8


def test_remove_credits_creates_negative_credit_record(admin_client, test_user):
    """Test that removing credits creates a Credit record with negative amount"""
    from app.models import Credit

    initial_count = Credit.query.filter_by(user_id=test_user.id).count()

    admin_client.post(
        f"/admin/members/{test_user.id}/credits/adjust",
        data={"quantity": "2", "reason": "Error correction", "action": "remove"},
        follow_redirects=True,
    )

    credits = Credit.query.filter_by(user_id=test_user.id).all()
    assert len(credits) == initial_count + 1
    new_credit = credits[-1]
    assert new_credit.amount == -2
    assert new_credit.reason == "Error correction"
    assert new_credit.payment_id is None


def test_add_credits_invalid_quantity(admin_client, test_user):
    """Test adding credits with invalid quantity shows error"""
    initial_credits = test_user.membership.purchased_credits

    response = admin_client.post(
        f"/admin/members/{test_user.id}/credits/adjust",
        data={"quantity": "0", "action": "add"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"valid number" in response.data

    db.session.refresh(test_user)
    assert test_user.membership.purchased_credits == initial_credits


def test_add_credits_no_membership(admin_client, app):
    """Test adding credits to member without membership shows error"""
    user = User(
        name="No Membership User",
        email="nomembership2@example.com",
        qualification="none",
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    response = admin_client.post(
        f"/admin/members/{user.id}/credits/adjust",
        data={"quantity": "5", "action": "add"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"does not have a membership" in response.data


def test_add_credits_requires_permission(member_client, test_user):
    """Test that adjusting credits requires members.manage_membership permission"""
    response = member_client.post(f"/admin/members/{test_user.id}/credits/adjust", data={"quantity": "5", "action": "add"})
    assert response.status_code == 403


def test_member_detail_shows_adjust_credits_form(admin_client, test_user):
    """Test that member detail page shows adjust credits controls for admin"""
    response = admin_client.get(f"/admin/members/{test_user.id}")
    assert response.status_code == 200
    assert b"Adjust Credits" in response.data


def test_adjust_credits_stores_adjusted_by(admin_client, admin_user, test_user):
    """Test that adjusting credits records which admin made the change"""
    from app.models import Credit

    admin_client.post(
        f"/admin/members/{test_user.id}/credits/adjust",
        data={"quantity": "1", "action": "add", "reason": "Test"},
        follow_redirects=True,
    )

    credit = Credit.query.filter_by(user_id=test_user.id).order_by(Credit.id.desc()).first()
    assert credit is not None
    assert credit.adjusted_by_id == admin_user.id


def test_members_requires_admin(member_client, test_user):
    """Test that members list requires admin"""
    response = member_client.get("/admin/members")
    assert response.status_code in [302, 403]


def test_member_detail_not_found(admin_client):
    """Test viewing non-existent member"""
    response = admin_client.get("/admin/members/99999")
    assert response.status_code == 404


def test_renew_membership(admin_client, test_user, app):
    """Test renewing a member's membership"""
    response = admin_client.post(
        f"/admin/members/{test_user.id}/membership/renew",
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_renew_membership_nonexistent(admin_client):
    """Test renewing a non-existent member returns 404"""
    response = admin_client.post("/admin/members/99999/membership/renew")
    assert response.status_code == 404


def test_deactivate_member(admin_client, test_user):
    """Test deactivating a member via admin"""
    response = admin_client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": test_user.name,
            "email": test_user.email,
            "is_active": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_activate_member(admin_client, test_user):
    """Test activating a member via admin"""
    response = admin_client.post(
        f"/admin/members/{test_user.id}/edit",
        data={
            "name": test_user.name,
            "email": test_user.email,
            "is_active": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_activate_user_success(admin_client, test_user, mocker):
    """Test activating inactive user sends welcome email"""
    mock_send_email = mocker.patch("app.services.mail_service.MailService.send_welcome_email")

    test_user.is_active = False
    from app import db

    db.session.commit()

    response = admin_client.post(f"/admin/members/{test_user.id}/activate", follow_redirects=True)

    assert response.status_code == 200
    assert b"Account activated" in response.data
    assert b"Welcome email sent" in response.data

    from app.models import User

    user = db.session.get(User, test_user.id)
    assert user.is_active is True

    mock_send_email.assert_called_once_with(test_user.id)


def test_activate_user_already_active(admin_client, test_user):
    """Test activating already active user shows warning"""
    test_user.is_active = True
    from app import db

    db.session.commit()

    response = admin_client.post(f"/admin/members/{test_user.id}/activate", follow_redirects=True)

    assert response.status_code == 200
    assert b"already active" in response.data


def test_activate_user_not_found(admin_client):
    """Test activating non-existent user returns 404"""
    response = admin_client.post("/admin/members/99999/activate", follow_redirects=False)

    assert response.status_code == 404
