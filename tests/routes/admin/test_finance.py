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
