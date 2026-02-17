"""Tests for admin cash payment approval routes"""

from unittest.mock import patch

from app import db
from app.models import Credit
from tests.helpers import create_payment_for_user


def test_pending_payments_page_requires_permission(client, test_user):
    """Test that pending payments page requires payments.approve permission"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/payments")
    assert response.status_code == 403


def test_pending_payments_page_accessible_to_admin(client, admin_user):
    """Test that admin can access pending payments page"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/payments")
    assert response.status_code == 200
    assert b"Pending Cash Payments" in response.data


def test_pending_payments_shows_cash_payments(client, admin_user, test_user):
    """Test that pending cash payments are shown in the list"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create a pending cash payment
    create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
        description="Annual Membership (Cash)",
    )

    response = client.get("/admin/payments")
    assert response.status_code == 200
    assert test_user.name.encode() in response.data
    assert b"Membership" in response.data


def test_pending_payments_does_not_show_online_payments(client, admin_user, test_user):
    """Test that online payments are not shown in pending cash list"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create a pending online payment (should not appear)
    create_payment_for_user(
        db,
        test_user,
        payment_method="online",
        status="pending",
        payment_type="membership",
    )

    response = client.get("/admin/payments")
    assert response.status_code == 200
    # Should show empty state
    assert b"No pending payments" in response.data


@patch("app.services.mail_service.send_payment_receipt")
def test_approve_membership_payment(mock_send_receipt, client, admin_user, test_user):
    """Test approving a cash membership payment activates membership"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Set membership to pending
    test_user.membership.status = "pending"
    db.session.commit()

    # Create a pending cash payment
    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
        description="Annual Membership (Cash)",
    )

    response = client.post(f"/admin/payments/{payment.id}/approve", follow_redirects=True)

    assert response.status_code == 200
    assert b"Payment approved" in response.data

    # Verify payment was completed
    db.session.refresh(payment)
    assert payment.status == "completed"
    assert payment.payment_processor == "cash"

    # Verify membership was activated
    db.session.refresh(test_user)
    assert test_user.membership.status == "active"

    # Verify email was sent
    mock_send_receipt.assert_called_once()


@patch("app.services.mail_service.send_credit_purchase_receipt")
def test_approve_credits_payment(mock_send_receipt, client, admin_user, test_user):
    """Test approving a cash credits payment adds credits"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    initial_credits = test_user.membership.purchased_credits

    # Create a pending cash credits payment
    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
        payment_type="credits",
        description="5 shooting credits (Cash)",
        amount_cents=2500,
    )

    response = client.post(f"/admin/payments/{payment.id}/approve", follow_redirects=True)

    assert response.status_code == 200
    assert b"Payment approved" in response.data

    # Verify payment was completed
    db.session.refresh(payment)
    assert payment.status == "completed"

    # Verify credits were added
    db.session.refresh(test_user)
    assert test_user.membership.purchased_credits == initial_credits + 5

    # Verify credit record was created
    credit = Credit.query.filter_by(user_id=test_user.id, payment_id=payment.id).first()
    assert credit is not None
    assert credit.amount == 5

    # Verify email was sent
    mock_send_receipt.assert_called_once()


def test_approve_payment_not_found(client, admin_user):
    """Test approving non-existent payment returns 404"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post("/admin/payments/99999/approve")
    assert response.status_code == 404


def test_approve_already_completed_payment(client, admin_user, test_user):
    """Test cannot approve already completed payment"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create an already completed payment
    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="completed",
        payment_type="membership",
    )

    response = client.post(f"/admin/payments/{payment.id}/approve", follow_redirects=True)

    assert response.status_code == 200
    assert b"cannot be approved" in response.data


def test_approve_online_payment_fails(client, admin_user, test_user):
    """Test cannot approve online payment via this route"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create an online pending payment
    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="online",
        status="pending",
        payment_type="membership",
    )

    response = client.post(f"/admin/payments/{payment.id}/approve", follow_redirects=True)

    assert response.status_code == 200
    assert b"cannot be approved" in response.data


def test_reject_payment(client, admin_user, test_user):
    """Test rejecting a cash payment"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create a pending cash payment
    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )

    response = client.post(f"/admin/payments/{payment.id}/reject", follow_redirects=True)

    assert response.status_code == 200
    assert b"Payment rejected" in response.data

    # Verify payment was cancelled
    db.session.refresh(payment)
    assert payment.status == "cancelled"


def test_reject_payment_not_found(client, admin_user):
    """Test rejecting non-existent payment returns 404"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post("/admin/payments/99999/reject")
    assert response.status_code == 404


def test_reject_completed_payment_fails(client, admin_user, test_user):
    """Test cannot reject already completed payment"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create a completed payment
    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="completed",
        payment_type="membership",
    )

    response = client.post(f"/admin/payments/{payment.id}/reject", follow_redirects=True)

    assert response.status_code == 200
    assert b"cannot be rejected" in response.data


def test_approve_requires_permission(client, test_user):
    """Test that approve requires payments.approve permission"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    # Create a pending cash payment
    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )

    response = client.post(f"/admin/payments/{payment.id}/approve")
    assert response.status_code == 403


def test_reject_requires_permission(client, test_user):
    """Test that reject requires payments.approve permission"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    # Create a pending cash payment
    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )

    response = client.post(f"/admin/payments/{payment.id}/reject")
    assert response.status_code == 403


def test_dashboard_shows_pending_payments_count(client, admin_user, test_user):
    """Test that admin dashboard shows pending cash payments count"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create pending cash payments
    for i in range(3):
        create_payment_for_user(
            db,
            test_user,
            payment_method="cash",
            status="pending",
            payment_type="membership",
            description=f"Payment {i}",
        )

    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert b"Pending Cash Payments" in response.data


@patch("app.services.mail_service.send_payment_receipt")
def test_approve_payment_with_redirect(mock_send_receipt, client, admin_user, test_user):
    """Test approving payment with redirect_to parameter"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create a pending cash membership payment
    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
        description="Annual Membership (Cash)",
    )

    # Approve with redirect_to parameter
    response = client.post(
        f"/admin/payments/{payment.id}/approve",
        data={"redirect_to": f"/admin/members/{test_user.id}"},
        follow_redirects=False,
    )

    # Should redirect to member detail page
    assert response.status_code == 302
    assert f"/admin/members/{test_user.id}" in response.location


def test_reject_payment_with_redirect(client, admin_user, test_user):
    """Test rejecting payment with redirect_to parameter"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create a pending cash payment
    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )

    # Reject with redirect_to parameter
    response = client.post(
        f"/admin/payments/{payment.id}/reject",
        data={"redirect_to": f"/admin/members/{test_user.id}"},
        follow_redirects=False,
    )

    # Should redirect to member detail page
    assert response.status_code == 302
    assert f"/admin/members/{test_user.id}" in response.location


def test_member_detail_shows_approve_button_for_pending_cash_payment(
    client, admin_user, test_user
):
    """Test that member detail page shows approve button for pending cash payments"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Create a pending cash payment
    create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )

    response = client.get(f"/admin/members/{test_user.id}")
    assert response.status_code == 200
    assert b"Approve" in response.data
    assert b"Reject" in response.data
