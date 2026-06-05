from tests.helpers import create_payment_for_user


def test_dashboard_stats_includes_pending_payments(app, admin_user, test_user):
    from app import db
    from app.services import admin

    create_payment_for_user(
        db,
        user=test_user,
        payment_method="cash",
        status="pending",
        payment_type="membership",
    )
    result = admin.get_dashboard_stats()
    assert result.success is True
    assert result.data["pending_cash_payments"] >= 1
    assert len(result.data["pending_payments_data"]) >= 1
