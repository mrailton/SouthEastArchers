"""Payment routes — auth gates, session wiring, and checkout HTTP behaviour."""

from unittest.mock import Mock, patch

import pytest

from app import db
from app.models import Payment
from app.services.result import ServiceResult
from tests.http_helpers import set_session


@patch("app.routes.payment.SumUpService")
@patch("app.services.mail.send_payment_receipt")
def test_complete_checkout_signup_payment(mock_email, mock_sumup_class, member_client, test_user):
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    mock_checkout = Mock(status="PAID", transaction_code="TXN123", transaction_id="txn_123")
    mock_sumup_class.return_value.get_checkout.return_value = mock_checkout

    set_session(
        member_client,
        signup_user_id=test_user.id,
        signup_payment_id=payment.id,
    )
    response = member_client.post("/payment/checkout/test_123/complete", follow_redirects=True)

    assert response.status_code == 200
    assert b"Payment successful" in response.content


@patch("app.routes.payment.SumUpService")
def test_complete_checkout_failed_status(mock_sumup_class, member_client):
    mock_sumup_class.return_value.get_checkout.return_value = Mock(status="FAILED", transaction_code=None, transaction_id=None)
    response = member_client.post("/payment/checkout/test_123/complete", follow_redirects=True)
    assert b"Payment declined" in response.content


@patch("app.routes.payment.SumUpService")
@patch("app.services.mail.send_payment_receipt")
def test_complete_checkout_membership_renewal(mock_email, mock_sumup_class, member_client, test_user):
    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    mock_sumup_class.return_value.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN", transaction_id="txn_456")
    set_session(
        member_client,
        membership_renewal_user_id=test_user.id,
        membership_renewal_payment_id=payment.id,
    )
    response = member_client.post("/payment/checkout/test_123/complete", follow_redirects=True)
    assert response.status_code == 200
    assert b"successfully" in response.content.lower()


@patch("app.routes.payment.SumUpService")
def test_complete_checkout_null_checkout(mock_sumup_class, member_client):
    mock_sumup_class.return_value.get_checkout.return_value = None
    response = member_client.post("/payment/checkout/test_123/complete", follow_redirects=True)
    assert b"Could not verify payment status" in response.content


def test_checkout_page_displays_session_data(member_client):
    set_session(member_client, checkout_amount=100.00, checkout_description="Test Payment")
    response = member_client.get("/payment/checkout/test_checkout_123")
    assert response.status_code == 200
    assert b"test_checkout_123" in response.content


@pytest.mark.parametrize("path", ["/payment/membership", "/payment/credits", "/payment/history"])
def test_payment_pages_require_login(client, path):
    response = client.get(path, follow_redirects=True)
    assert b"Login" in response.content


@patch("app.routes.payment.payment_service.initiate_membership_payment")
def test_membership_payment_redirects_to_checkout(mock_initiate, member_client, test_user):
    mock_initiate.return_value = ServiceResult.ok(
        data={
            "checkout_id": "checkout_abc",
            "payment_id": 1,
            "user_id": test_user.id,
            "amount": 100.0,
            "description": "Annual Membership",
        }
    )
    response = member_client.post("/payment/membership", follow_redirects=False)
    assert response.status_code in (302, 303)
    assert "/payment/checkout/" in response.headers.get("location", "")


@pytest.mark.parametrize(
    "path,quantity,expected",
    [
        ("/payment/credits", "0", b"Quantity must be between 1 and 50"),
        ("/payment/credits", "51", b"Quantity must be between 1 and 50"),
        ("/payment/credits", "abc", b"Invalid quantity"),
        ("/payment/credits/cash", "0", b"Quantity must be between 1 and 50"),
    ],
)
def test_credits_purchase_rejects_invalid_quantity(member_client, path, quantity, expected):
    response = member_client.post(path, data={"quantity": quantity}, follow_redirects=True)
    assert expected in response.content


@patch("app.services.mail.send_cash_payment_pending_email")
def test_membership_cash_payment_renders_pending_page(mock_send_email, member_client):
    response = member_client.post("/payment/membership/cash", follow_redirects=True)
    assert response.status_code == 200
    assert b"Cash Payment Pending" in response.content
