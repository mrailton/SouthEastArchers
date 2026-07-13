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


@patch("app.services.mail.send_payment_receipt")
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


def test_approve_completed_payment_is_idempotent(admin_client, test_user):
    payment = create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="completed",
        payment_type="membership",
    )
    response = admin_client.post(f"/admin/payments/{payment.id}/approve", follow_redirects=True)
    assert b"Payment approved" in response.content


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


@patch("app.services.payment_processing.SumUpService")
def test_reconcile_payment_fulfills_and_records_ledger(mock_sumup_class, admin_client, test_user, fake_mailer):
    from unittest.mock import Mock

    from app import db
    from app.events.background import flush_deferred_handlers
    from app.models import FinancialTransaction, Payment
    from app.services import settings

    settings.set("sumup_fee_percentage", "2.5")

    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="pending",
        sumup_checkout_id="chk_reconcile_e2e",
    )
    db.session.add(payment)
    db.session.commit()

    mock_sumup_class.return_value.get_checkout.return_value = Mock(
        status="PAID",
        transaction_code="TXN_E2E",
        transaction_id="txn_e2e",
    )

    response = admin_client.post(f"/admin/payments/{payment.id}/reconcile", follow_redirects=True)

    assert response.status_code == 200
    assert b"renewed successfully" in response.content.lower() or b"successfully" in response.content.lower()

    flush_deferred_handlers()
    db.session.refresh(payment)
    assert payment.status == "completed"

    txns = FinancialTransaction.query.filter_by(category="membership_fees", type="income").all()
    assert len(txns) == 1
    assert len(fake_mailer.sent_messages) >= 1


def test_reconcile_payments_page_lists_unfulfilled_online(admin_client, test_user):
    create_payment_for_user(
        db,
        user=test_user,
        payment_method="online",
        status="pending",
        payment_type="membership",
        sumup_checkout_id="chk_list",
    )
    response = admin_client.get("/admin/payments/reconcile")
    assert response.status_code == 200
    assert b"chk_list" in response.content


def test_reconcile_payment_not_found(admin_client):
    response = admin_client.post("/admin/payments/99999/reconcile")
    assert response.status_code == 404


def test_reconcile_payment_rejects_external_redirect(admin_client, test_user):
    payment = create_payment_for_user(
        db,
        user=test_user,
        payment_method="online",
        status="pending",
        sumup_checkout_id="chk_redirect",
    )
    with patch("app.services.payment_processing.reconcile_sumup_payment") as mock_reconcile:
        from app.services.result import ServiceResult

        mock_reconcile.return_value = ServiceResult.fail("Not paid")
        response = admin_client.post(
            f"/admin/payments/{payment.id}/reconcile",
            data={"redirect_to": "https://evil.example"},
            follow_redirects=False,
        )
    assert response.status_code in (302, 303)
    assert "/admin/payments/reconcile" in response.headers.get("location", "")


def test_approve_payment_rejects_external_redirect(admin_client, test_user):
    payment = create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="pending",
    )
    with patch("app.services.payments.approve_cash_payment") as mock_approve:
        from app.services.result import ServiceResult

        mock_approve.return_value = ServiceResult.fail("nope")
        response = admin_client.post(
            f"/admin/payments/{payment.id}/approve",
            data={"redirect_to": "https://evil.example"},
            follow_redirects=False,
        )
    assert response.status_code in (302, 303)
    assert "/admin/payments" in response.headers.get("location", "")


def test_reject_payment_not_found(admin_client):
    response = admin_client.post("/admin/payments/99999/reject")
    assert response.status_code == 404


def test_reject_payment_rejects_external_redirect(admin_client, test_user):
    payment = create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="pending",
    )
    with patch("app.services.payments.reject_cash_payment") as mock_reject:
        from app.services.result import ServiceResult

        mock_reject.return_value = ServiceResult.ok(message="rejected")
        response = admin_client.post(
            f"/admin/payments/{payment.id}/reject",
            data={"redirect_to": "https://evil.example"},
            follow_redirects=False,
        )
    assert response.status_code in (302, 303)
    assert "/admin/payments" in response.headers.get("location", "")


def test_replay_payment_side_effects_from_form(admin_client, test_user, fake_mailer):
    payment = create_payment_for_user(
        db,
        user=test_user,
        status="completed",
        payment_type="membership",
        payment_method="cash",
        payment_processor="cash",
    )
    response = admin_client.post(
        "/admin/payments/replay-side-effects",
        data={"payment_id": str(payment.id), "redirect_to": "/admin/payments/reconcile"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"replayed successfully" in response.content.lower()


def test_replay_payment_side_effects_rejects_invalid_id(admin_client):
    response = admin_client.post(
        "/admin/payments/replay-side-effects",
        data={"payment_id": "not-a-number", "redirect_to": "/admin/payments/reconcile"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"valid payment id" in response.content.lower()


def test_replay_payment_side_effects_not_found(admin_client):
    response = admin_client.post("/admin/payments/99999/replay-side-effects")
    assert response.status_code == 404


def test_replay_payment_side_effects_by_id(admin_client, test_user, fake_mailer):
    payment = create_payment_for_user(
        db,
        user=test_user,
        status="completed",
        payment_type="membership",
        payment_method="cash",
        payment_processor="cash",
    )
    response = admin_client.post(
        f"/admin/payments/{payment.id}/replay-side-effects",
        data={"redirect_to": "/admin/payments/reconcile"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"replayed successfully" in response.content.lower()


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


def test_cancel_payment_success(admin_client, test_user):
    payment = create_payment_for_user(db, test_user, status="pending", payment_method="online")
    response = admin_client.post(
        f"/admin/payments/{payment.id}/cancel",
        data={"redirect_to": f"/admin/members/{test_user.id}"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    db.session.refresh(payment)
    assert payment.status == "cancelled"


def test_cancel_payment_not_found_returns_404(admin_client):
    response = admin_client.post(
        "/admin/payments/999999/cancel",
        data={"redirect_to": "/admin/payments"},
    )
    assert response.status_code == 404


def test_cancel_payment_requires_permission(member_client, test_user):
    payment = create_payment_for_user(db, test_user, status="pending", payment_method="online")
    response = member_client.post(f"/admin/payments/{payment.id}/cancel")
    assert response.status_code == 403
