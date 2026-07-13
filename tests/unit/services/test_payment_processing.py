from unittest.mock import Mock, patch

import pytest

from app.services.payment_processing import fulfill_checkout


@pytest.fixture
def mock_sumup():
    service = Mock()
    with patch("app.services.payment_processing.SumUpService", return_value=service):
        yield service


@pytest.mark.parametrize(
    "status,expected_category,message_fragment,expected_redirect",
    [
        ("FAILED", "error", "declined", "/member/dashboard"),
        ("PENDING", "warning", "pending", "/payment/checkout/chk_1"),
        ("CANCELLED", "error", "not completed", "/member/dashboard"),
    ],
)
def test_fulfill_checkout_non_paid_status(mock_sumup, status, expected_category, message_fragment, expected_redirect):
    mock_sumup.get_checkout.return_value = Mock(status=status)

    result = fulfill_checkout(checkout_id="chk_1", session={}, user_id=1, sumup=mock_sumup)

    assert result.success is True
    assert result.data is not None
    assert result.data.flash_category == expected_category
    assert message_fragment in result.data.flash_message
    assert result.data.redirect_url == expected_redirect


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


def test_fulfill_checkout_fallback_routes_inactive_user_via_signup_handler(app, test_user, mock_sumup):
    """Inactive user with a matching pending payment should be processed via handle_signup_payment."""
    from app import db
    from app.models import Payment

    test_user.is_active = False
    db.session.commit()

    payment = Payment(
        user_id=test_user.id,
        amount_cents=10000,
        currency="EUR",
        payment_type="membership",
        payment_method="online",
        status="pending",
        sumup_checkout_id="chk_inactive",
    )
    db.session.add(payment)
    db.session.commit()

    mock_sumup.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN_INACTIVE", transaction_id="txn_inactive")

    with patch("app.services.payment_processing.handle_signup_payment") as mock_handle:
        from app.services.result import ServiceResult

        mock_handle.return_value = ServiceResult.ok(message="Payment successful!")
        result = fulfill_checkout(checkout_id="chk_inactive", session={}, user_id=test_user.id, sumup=mock_sumup)

    assert result.success is True
    assert result.data is not None
    assert result.data.flash_category == "success"
    mock_handle.assert_called_once_with(test_user.id, payment.id, "TXN_INACTIVE")


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


def test_reconcile_sumup_payment_checkout_unreachable(app, test_user):
    """SumUp returns None (network/API error) → reconcile fails gracefully."""
    from unittest.mock import Mock

    from app import db
    from app.services import payment_processing
    from tests.helpers import create_payment_for_user

    payment = create_payment_for_user(
        db,
        test_user,
        status="pending",
        payment_method="online",
        sumup_checkout_id="chk_unreachable",
    )
    mock_sumup = Mock()
    mock_sumup.get_checkout.return_value = None

    result = payment_processing.reconcile_sumup_payment(payment.id, sumup=mock_sumup)

    assert result.success is False
    assert "Could not verify" in result.message


def test_fulfill_checkout_membership_renewal_non_int_payment_id(mock_sumup):
    """Non-integer payment_id in session (e.g. stale stringified value) returns a failure."""
    from app.services.payment_processing import fulfill_checkout

    mock_sumup.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN", transaction_id="txn")

    session = {"membership_renewal_user_id": 1, "membership_renewal_payment_id": "not-an-int"}
    result = fulfill_checkout(checkout_id="chk_bad_id", session=session, user_id=1, sumup=mock_sumup)

    assert result.success is False
    assert "session" in result.message.lower()


def test_fulfill_checkout_credit_purchase_string_quantity(mock_sumup):
    """String credit_purchase_quantity in session is cast to int before dispatch."""
    from unittest.mock import patch

    from app.services.payment_processing import fulfill_checkout
    from app.services.result import ServiceResult

    mock_sumup.get_checkout.return_value = Mock(status="PAID", transaction_code="TXN", transaction_id="txn")

    session = {
        "credit_purchase_user_id": 8,
        "credit_purchase_payment_id": 55,
        "credit_purchase_quantity": "3",  # string, not int
    }
    with patch("app.services.payment_processing.handle_credit_purchase") as mock_handle:
        mock_handle.return_value = ServiceResult.ok(message="Done")
        result = fulfill_checkout(checkout_id="chk_str_qty", session=session, user_id=8, sumup=mock_sumup)

    assert result.success is True
    mock_handle.assert_called_once_with(8, 55, 3, "TXN")  # quantity cast to int


# ---------------------------------------------------------------------------
# _mark_checkout_payment_failed
# ---------------------------------------------------------------------------


def test_fulfill_checkout_failed_marks_payment_failed(app, test_user, mock_sumup):
    """When SumUp status is FAILED, the linked DB payment is marked failed."""
    from app import db
    from app.services.payment_processing import fulfill_checkout
    from tests.helpers import create_payment_for_user

    payment = create_payment_for_user(db, test_user, status="pending", payment_method="online", sumup_checkout_id="chk_fail")
    mock_sumup.get_checkout.return_value = Mock(status="FAILED")

    result = fulfill_checkout(checkout_id="chk_fail", session={}, user_id=test_user.id, sumup=mock_sumup)

    db.session.refresh(payment)
    assert result.success is True
    assert result.data.redirect_url == "/member/dashboard"
    assert result.data.flash_category == "error"
    assert payment.status == "failed"


def test_fulfill_checkout_failed_clears_all_session_keys(app, mock_sumup):
    """Failed checkout clears all checkout session keys."""
    from app.services.payment_processing import _ALL_CHECKOUT_SESSION_KEYS, fulfill_checkout

    mock_sumup.get_checkout.return_value = Mock(status="FAILED")

    result = fulfill_checkout(checkout_id="chk_fail_keys", session={}, user_id=1, sumup=mock_sumup)

    assert result.success is True
    assert set(result.data.session_keys_to_clear) == set(_ALL_CHECKOUT_SESSION_KEYS)
