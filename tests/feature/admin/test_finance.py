"""Admin finance routes — permissions, statements, and PDF download."""

from datetime import date

from app import db
from app.models import FinancialTransaction


def _seed_transaction(admin_user, *, txn_type: str) -> None:
    db.session.add(
        FinancialTransaction(
            type=txn_type,
            date=date(2026, 1, 15),
            amount_cents=5000,
            category="equipment" if txn_type == "expense" else "membership_fees",
            description=f"Test {txn_type}",
            created_by_id=admin_user.id,
        )
    )
    db.session.commit()


def test_finance_list(admin_client):
    response = admin_client.get("/admin/finance")
    assert response.status_code == 200


def test_create_expense_redirects(admin_client):
    response = admin_client.post(
        "/admin/finance/expense/create",
        data={
            "date": "2026-01-15",
            "amount": "50.00",
            "category": "equipment",
            "description": "New arrows",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)


def test_financial_statement_generate(admin_client, admin_user):
    _seed_transaction(admin_user, txn_type="income")
    response = admin_client.post(
        "/admin/finance/statement",
        data={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )
    assert response.status_code == 200
    assert b"Total Income" in response.content


def test_financial_statement_end_before_start(admin_client):
    response = admin_client.post(
        "/admin/finance/statement",
        data={"start_date": "2026-02-01", "end_date": "2026-01-01"},
    )
    assert b"End date must be after start date" in response.content


def test_financial_statement_pdf_download(admin_client, admin_user):
    _seed_transaction(admin_user, txn_type="expense")
    response = admin_client.get("/admin/finance/statement/pdf?start_date=2026-01-01&end_date=2026-01-31")
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/pdf"
    assert response.content[:5] == b"%PDF-"


def test_finance_requires_admin(member_client):
    response = member_client.get("/admin/finance")
    assert response.status_code in (302, 403)


def test_create_expense_page(admin_client):
    response = admin_client.get("/admin/finance/expense/create")
    assert response.status_code == 200


def test_create_income_redirects(admin_client):
    response = admin_client.post(
        "/admin/finance/income/create",
        data={
            "date": "2026-01-20",
            "amount": "75.00",
            "category": "donations",
            "description": "Club donation",
            "source": "Local sponsor",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)


def test_create_income_page(admin_client):
    response = admin_client.get("/admin/finance/income/create")
    assert response.status_code == 200


def test_financial_statement_page_defaults(admin_client):
    response = admin_client.get("/admin/finance/statement")
    assert response.status_code == 200
    assert b"start_date" in response.content


def test_financial_statement_defaults_use_membership_year_start(app, admin_client):
    """Statement page pre-fills start_date from the configured membership year, not hardcoded March."""
    from app.services import settings

    settings.set("membership_year_start_month", 9)
    settings.set("membership_year_start_day", 1)

    response = admin_client.get("/admin/finance/statement")
    assert response.status_code == 200
    # The pre-filled start date should be September, not March
    assert b"09-01" in response.content or b'value="2025-09-01"' in response.content or b"2025-09-01" in response.content


def test_financial_statement_validation_error(admin_client):
    response = admin_client.post("/admin/finance/statement", data={"start_date": "", "end_date": ""})
    assert response.status_code == 422


def test_financial_statement_pdf_missing_dates(admin_client):
    response = admin_client.get("/admin/finance/statement/pdf", follow_redirects=True)
    assert b"Please provide start and end dates" in response.content


def test_financial_statement_pdf_invalid_dates(admin_client):
    response = admin_client.get(
        "/admin/finance/statement/pdf?start_date=not-a-date&end_date=2026-01-31",
        follow_redirects=True,
    )
    assert b"Invalid date format" in response.content


def test_edit_transaction_expense(admin_client, admin_user):
    _seed_transaction(admin_user, txn_type="expense")
    from app.models import FinancialTransaction

    txn = FinancialTransaction.query.first()
    response = admin_client.get(f"/admin/finance/{txn.id}/edit")
    assert response.status_code == 200

    response = admin_client.post(
        f"/admin/finance/{txn.id}/edit",
        data={
            "date": "2026-01-16",
            "amount": "60.00",
            "category": "supplies",
            "description": "Updated expense",
            "receipt_reference": "INV-1",
        },
        follow_redirects=True,
    )
    assert b"Transaction updated successfully" in response.content


def test_edit_transaction_income(admin_client, admin_user):
    _seed_transaction(admin_user, txn_type="income")
    from app.models import FinancialTransaction

    txn = FinancialTransaction.query.filter_by(type="income").first()
    response = admin_client.post(
        f"/admin/finance/{txn.id}/edit",
        data={
            "date": "2026-01-16",
            "amount": "80.00",
            "category": "membership_fees",
            "description": "Updated income",
            "source": "Member",
        },
        follow_redirects=True,
    )
    assert b"Transaction updated successfully" in response.content


def test_delete_transaction(admin_client, admin_user):
    _seed_transaction(admin_user, txn_type="expense")
    from app.models import FinancialTransaction

    txn = FinancialTransaction.query.first()
    response = admin_client.post(f"/admin/finance/{txn.id}/delete", follow_redirects=True)
    assert b"Transaction deleted" in response.content


def test_edit_transaction_not_found(admin_client):
    response = admin_client.get("/admin/finance/99999/edit")
    assert response.status_code == 404
