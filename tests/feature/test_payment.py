"""Payment routes — auth gates, session wiring, and checkout HTTP behaviour."""

from unittest.mock import Mock, patch

import pytest

from app import db
from app.models import Payment
from app.services.result import ServiceResult
from tests.http_helpers import set_session


@patch("app.services.payment_processing.SumUpService")
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


@patch("app.services.payment_processing.SumUpService")
def test_complete_checkout_failed_status(mock_sumup_class, member_client):
    mock_sumup_class.return_value.get_checkout.return_value = Mock(status="FAILED", transaction_code=None, transaction_id=None)
    response = member_client.post("/payment/checkout/test_123/complete", follow_redirects=True)
    assert b"Payment declined" in response.content


@patch("app.services.payment_processing.SumUpService")
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


@patch("app.services.payment_processing.SumUpService")
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


def test_membership_payment_page(member_client):
    response = member_client.get("/payment/membership")
    assert response.status_code == 200


@patch("app.routes.payment.payment_service.initiate_membership_payment")
def test_membership_payment_failure_renders_page(mock_initiate, member_client):
    mock_initiate.return_value = ServiceResult.fail("Payment failed")
    response = member_client.post("/payment/membership")
    assert response.status_code == 422
    assert b"Payment failed" in response.content


def test_credits_page(member_client):
    response = member_client.get("/payment/credits")
    assert response.status_code == 200


def test_credits_page_without_membership(client, app):
    from app import db
    from app.models import User

    user = User(name="No Mem", email="nomem@example.com", phone="1", is_active=True)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    from tests.http_helpers import login

    login(client, "nomem@example.com", "password123")
    response = client.get("/payment/credits", follow_redirects=True)
    assert b"active membership" in response.content.lower()


@patch("app.routes.payment.payment_service.initiate_credit_purchase")
def test_credits_payment_checkout_redirect(mock_initiate, member_client, test_user):
    mock_initiate.return_value = ServiceResult.ok(
        data={
            "checkout_id": "checkout_credits",
            "user_id": test_user.id,
            "payment_id": 99,
            "quantity": 3,
            "amount": 15.0,
            "description": "3 credits",
        }
    )
    response = member_client.post("/payment/credits", data={"quantity": "3"}, follow_redirects=False)
    assert response.status_code in (302, 303)
    assert "checkout_credits" in response.headers.get("location", "")


@patch("app.services.mail.send_cash_payment_pending_email")
def test_credits_cash_payment_success(mock_send_email, member_client):
    response = member_client.post("/payment/credits/cash", data={"quantity": "2"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Cash Payment Pending" in response.content


def test_payment_history_page(member_client):
    response = member_client.get("/payment/history")
    assert response.status_code == 200


@patch("app.services.payment_processing.SumUpService")
def test_complete_checkout_pending_status(mock_sumup_class, member_client):
    mock_sumup_class.return_value.get_checkout.return_value = Mock(status="PENDING")
    response = member_client.post("/payment/checkout/test_123/complete", follow_redirects=True)
    assert b"pending" in response.content.lower()


@patch("app.services.payment_processing.SumUpService")
@patch("app.services.payment_processing.handle_credit_purchase")
def test_complete_checkout_credit_purchase(mock_handle, mock_sumup_class, member_client, test_user):
    from app import db
    from app.models import Payment

    payment = Payment(
        user_id=test_user.id,
        amount_cents=1500,
        currency="EUR",
        payment_type="credits",
        status="pending",
        description="3 shooting credits",
    )
    db.session.add(payment)
    db.session.commit()

    mock_sumup_class.return_value.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN", transaction_id="txn")
    mock_handle.return_value = ServiceResult.ok(message="Credits added")
    set_session(
        member_client,
        credit_purchase_user_id=test_user.id,
        credit_purchase_payment_id=payment.id,
        credit_purchase_quantity=3,
    )
    response = member_client.post("/payment/checkout/test_123/complete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Credits added" in response.content


@patch("app.routes.payment.payment_service.initiate_cash_membership_payment")
def test_membership_cash_payment_failure_redirect(mock_initiate, member_client):
    mock_initiate.return_value = ServiceResult.fail("Cash error")
    response = member_client.post("/payment/membership/cash", follow_redirects=True)
    assert b"Cash error" in response.content


@patch("app.routes.payment.payment_service.initiate_credit_purchase")
def test_credits_payment_failure(mock_initiate, member_client):
    mock_initiate.return_value = ServiceResult.fail("Credit error")
    response = member_client.post("/payment/credits", data={"quantity": "2"})
    assert b"Credit error" in response.content


@patch("app.routes.payment.payment_service.initiate_cash_credit_purchase")
def test_credits_cash_payment_failure(mock_initiate, member_client):
    mock_initiate.return_value = ServiceResult.fail("Cash credit error")
    response = member_client.post("/payment/credits/cash", data={"quantity": "2"}, follow_redirects=True)
    assert b"Cash credit error" in response.content


@patch("app.services.payment_processing.SumUpService")
def test_complete_checkout_generic_failure_status(mock_sumup_class, member_client):
    mock_sumup_class.return_value.get_checkout.return_value = Mock(status="UNKNOWN")
    response = member_client.post("/payment/checkout/test_123/complete", follow_redirects=True)
    assert b"not approved" in response.content.lower()


@patch("app.services.payment_processing.SumUpService")
def test_complete_checkout_missing_user_session(mock_sumup_class, member_client):
    mock_sumup_class.return_value.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN", transaction_id="txn")
    response = member_client.post("/payment/checkout/test_123/complete", follow_redirects=True)
    assert b"session not found" in response.content.lower() or b"Payment processed successfully" in response.content


@patch("app.services.payment_processing.SumUpService", side_effect=RuntimeError("boom"))
def test_complete_checkout_exception(mock_sumup_class, member_client):
    response = member_client.post("/payment/checkout/test_123/complete", follow_redirects=True)
    assert b"error occurred" in response.content.lower()
