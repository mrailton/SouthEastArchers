from unittest.mock import Mock, patch

import pytest

from app.services.payment_processing import fulfill_checkout


@pytest.fixture
def mock_sumup():
    service = Mock()
    with patch("app.services.payment_processing.SumUpService", return_value=service):
        yield service


@pytest.mark.parametrize(
    "status,expected_category,message_fragment",
    [
        ("FAILED", "error", "Payment declined"),
        ("PENDING", "warning", "pending"),
        ("CANCELLED", "error", "Payment failed"),
    ],
)
def test_fulfill_checkout_non_paid_status(mock_sumup, status, expected_category, message_fragment):
    mock_sumup.get_checkout.return_value = Mock(status=status)

    result = fulfill_checkout(checkout_id="chk_1", session={}, user_id=1, sumup=mock_sumup)

    assert result.success is True
    assert result.data is not None
    assert result.data.flash_category == expected_category
    assert message_fragment in result.data.flash_message
    assert result.data.redirect_url == "/payment/checkout/chk_1"


def test_fulfill_checkout_missing_checkout(mock_sumup):
    mock_sumup.get_checkout.return_value = None

    result = fulfill_checkout(checkout_id="chk_missing", session={}, user_id=1, sumup=mock_sumup)

    assert result.success is False
    assert "Could not verify payment status" in result.message


def test_fulfill_checkout_paid_without_session_user(mock_sumup):
    mock_sumup.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN1", transaction_id="txn_1")

    result = fulfill_checkout(checkout_id="chk_2", session={}, user_id=None, sumup=mock_sumup)

    assert result.success is True
    assert result.data is not None
    assert result.data.redirect_url == "/auth/login"
    assert result.data.flash_category == "error"


def test_fulfill_checkout_paid_without_flow_keys_warns_when_unmatched(app, mock_sumup):
    mock_sumup.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN2", transaction_id="txn_2")

    result = fulfill_checkout(checkout_id="chk_3", session={}, user_id=42, sumup=mock_sumup)

    assert result.success is True
    assert result.data is not None
    assert result.data.redirect_url == "/member/dashboard"
    assert result.data.flash_category == "warning"
    assert "could not be matched" in result.data.flash_message


@patch("app.services.payment_processing.handle_signup_payment")
def test_fulfill_checkout_signup_flow(mock_handle, mock_sumup):
    from app.services.result import ServiceResult

    mock_sumup.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN3", transaction_id="txn_3")
    mock_handle.return_value = ServiceResult.ok(message="Payment successful!")

    session = {"signup_user_id": 10, "signup_payment_id": 99}
    result = fulfill_checkout(checkout_id="chk_4", session=session, user_id=10, sumup=mock_sumup)

    assert result.success is True
    assert result.data is not None
    assert result.data.redirect_url == "/auth/login"
    assert result.data.flash_category == "success"
    mock_handle.assert_called_once_with(10, 99, "TXN3")


@patch("app.services.payment_processing.handle_membership_renewal")
def test_fulfill_checkout_membership_renewal_flow(mock_handle, mock_sumup):
    from app.services.result import ServiceResult

    mock_sumup.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN4", transaction_id="txn_4")
    mock_handle.return_value = ServiceResult.ok(message="Membership renewed successfully!")

    session = {"membership_renewal_user_id": 5, "membership_renewal_payment_id": 77}
    result = fulfill_checkout(checkout_id="chk_5", session=session, user_id=5, sumup=mock_sumup)

    assert result.success is True
    assert result.data is not None
    assert result.data.redirect_url == "/member/dashboard"
    mock_handle.assert_called_once_with(5, 77, "TXN4")


@patch("app.services.payment_processing.handle_credit_purchase")
def test_fulfill_checkout_credit_purchase_flow(mock_handle, mock_sumup):
    from app.services.result import ServiceResult

    mock_sumup.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN5", transaction_id="txn_5")
    mock_handle.return_value = ServiceResult.ok(message="Successfully purchased 3 credits!")

    session = {
        "credit_purchase_user_id": 8,
        "credit_purchase_payment_id": 55,
        "credit_purchase_quantity": 3,
    }
    result = fulfill_checkout(checkout_id="chk_6", session=session, user_id=8, sumup=mock_sumup)

    assert result.success is True
    assert result.data is not None
    assert "credit_purchase_quantity" in result.data.session_keys_to_clear
    mock_handle.assert_called_once_with(8, 55, 3, "TXN5")


def test_fulfill_checkout_paid_resolves_payment_by_checkout_id(app, test_user, mock_sumup):
    from app import db
    from app.models import Payment

    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="pending",
        sumup_checkout_id="chk_linked",
    )
    db.session.add(payment)
    db.session.commit()

    mock_sumup.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN_LINK", transaction_id="txn_link")

    with patch("app.services.payment_processing.handle_membership_renewal") as mock_handle:
        from app.services.result import ServiceResult

        mock_handle.return_value = ServiceResult.ok(message="Membership renewed successfully!")
        result = fulfill_checkout(checkout_id="chk_linked", session={}, user_id=test_user.id, sumup=mock_sumup)

    assert result.success is True
    assert result.data is not None
    assert result.data.flash_category == "success"
    mock_handle.assert_called_once_with(test_user.id, payment.id, "TXN_LINK")


@patch("app.services.payment_processing.SumUpService")
def test_reconcile_sumup_payment_fulfills_pending_payment(mock_sumup_class, app, test_user):
    from app import db
    from app.services import payment_processing
    from app.services.result import ServiceResult
    from tests.helpers import create_payment_for_user

    payment = create_payment_for_user(
        db,
        test_user,
        status="pending",
        payment_method="online",
        payment_type="membership",
        sumup_checkout_id="chk_admin_1",
    )
    mock_sumup_class.return_value.get_checkout.return_value = Mock(
        status="PAID",
        transaction_code="TXN_ADMIN",
        transaction_id="txn_admin",
    )

    with patch(
        "app.services.payment_processing.handle_membership_renewal",
        return_value=ServiceResult.ok(message="Membership renewed successfully!"),
    ) as mock_handle:
        result = payment_processing.reconcile_sumup_payment(payment.id, sumup=mock_sumup_class.return_value)

    assert result.success is True
    mock_handle.assert_called_once_with(test_user.id, payment.id, "TXN_ADMIN")


def test_reconcile_sumup_payment_not_found(app):
    from app.services import payment_processing
    from app.services.result import ErrorCode

    result = payment_processing.reconcile_sumup_payment(99999)
    assert result.success is False
    assert result.error_code == ErrorCode.NOT_FOUND


def test_reconcile_sumup_payment_rejects_non_online(app, test_user):
    from app import db
    from app.services import payment_processing
    from app.services.result import ErrorCode
    from tests.helpers import create_payment_for_user

    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="cash",
        status="pending",
    )
    result = payment_processing.reconcile_sumup_payment(payment.id)
    assert result.success is False
    assert result.error_code == ErrorCode.INVALID_STATE


def test_reconcile_sumup_payment_requires_checkout_id(app, test_user):
    from app import db
    from app.services import payment_processing
    from tests.helpers import create_payment_for_user

    payment = create_payment_for_user(
        db,
        test_user,
        payment_method="online",
        status="pending",
    )
    result = payment_processing.reconcile_sumup_payment(payment.id)
    assert result.success is False
    assert "No SumUp checkout" in result.message


def test_reconcile_sumup_payment_rejects_unpaid_checkout(app, test_user):
    from unittest.mock import Mock

    from app import db
    from app.services import payment_processing
    from tests.helpers import create_payment_for_user

    payment = create_payment_for_user(
        db,
        test_user,
        status="pending",
        payment_method="online",
        sumup_checkout_id="chk_pending",
    )
    mock_sumup = Mock()
    mock_sumup.get_checkout.return_value = Mock(status="PENDING")

    result = payment_processing.reconcile_sumup_payment(payment.id, sumup=mock_sumup)

    assert result.success is False
    assert "not paid" in result.message.lower()
