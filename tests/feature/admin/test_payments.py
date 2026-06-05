"""Admin cash payment routes — permissions, redirects, and flashes (approval logic: integration tests)."""

from unittest.mock import patch

from app import db
from tests.helpers import create_payment_for_user


def test_pending_payments_requires_permission(member_client):
    response = member_client.get("/admin/payments")
    assert response.status_code == 403


def test_pending_payments_lists_cash_payments(admin_client, test_user):
    create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
        description="Annual Membership (Cash)",
    )
    response = admin_client.get("/admin/payments")
    assert response.status_code == 200
    assert test_user.name.encode() in response.content


@patch("app.services.mail_service.MailService.send_payment_receipt")
def test_approve_payment_success_flash(mock_send_receipt, admin_client, test_user):
    payment = create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )
    response = admin_client.post(f"/admin/payments/{payment.id}/approve", follow_redirects=True)
    assert response.status_code == 200
    assert b"Payment approved" in response.content


def test_reject_payment_success_flash(admin_client, test_user):
    payment = create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )
    response = admin_client.post(f"/admin/payments/{payment.id}/reject", follow_redirects=True)
    assert response.status_code == 200
    assert b"Payment rejected" in response.content


def test_approve_payment_not_found(admin_client):
    response = admin_client.post("/admin/payments/99999/approve")
    assert response.status_code == 404


def test_approve_completed_payment_shows_error(admin_client, test_user):
    payment = create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="completed",
        payment_type="membership",
    )
    response = admin_client.post(f"/admin/payments/{payment.id}/approve", follow_redirects=True)
    assert b"cannot be approved" in response.content


def test_approve_requires_permission(member_client, test_user):
    payment = create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )
    response = member_client.post(f"/admin/payments/{payment.id}/approve")
    assert response.status_code == 403


def test_approve_payment_with_redirect(admin_client, test_user):
    payment = create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )
    response = admin_client.post(
        f"/admin/payments/{payment.id}/approve",
        data={"redirect_to": f"/admin/members/{test_user.id}"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert f"/admin/members/{test_user.id}" in response.headers.get("location", "")


def test_reject_payment_with_redirect(admin_client, test_user):
    payment = create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )
    response = admin_client.post(
        f"/admin/payments/{payment.id}/reject",
        data={"redirect_to": f"/admin/members/{test_user.id}"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert f"/admin/members/{test_user.id}" in response.headers.get("location", "")
