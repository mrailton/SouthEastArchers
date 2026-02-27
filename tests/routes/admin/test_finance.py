"""Tests for admin finance routes."""

from datetime import date

from app import db
from app.models import FinancialTransaction


def _login_admin(client, admin_user):
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})


def _create_expense(admin_user):
    txn = FinancialTransaction(
        type="expense",
        date=date(2026, 1, 15),
        amount_cents=5000,
        category="equipment",
        description="Test expense",
        created_by_id=admin_user.id,
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def _create_income(admin_user):
    txn = FinancialTransaction(
        type="income",
        date=date(2026, 1, 20),
        amount_cents=10000,
        category="membership_fees",
        description="Test income",
        created_by_id=admin_user.id,
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def test_finance_list(client, admin_user):
    """Test viewing finance list page."""
    _login_admin(client, admin_user)
    response = client.get("/admin/finance")
    assert response.status_code == 200
    assert b"Finance" in response.data


def test_finance_list_with_transactions(client, admin_user, app):
    """Test viewing finance list with existing transactions."""
    _login_admin(client, admin_user)
    _create_expense(admin_user)
    _create_income(admin_user)

    response = client.get("/admin/finance")
    assert response.status_code == 200
    assert b"Test expense" in response.data
    assert b"Test income" in response.data


def test_create_expense_page(client, admin_user):
    """Test accessing create expense page."""
    _login_admin(client, admin_user)
    response = client.get("/admin/finance/expense/create")
    assert response.status_code == 200
    assert b"Add Expense" in response.data


def test_create_expense_success(client, admin_user, app):
    """Test successfully creating an expense."""
    _login_admin(client, admin_user)

    response = client.post(
        "/admin/finance/expense/create",
        data={
            "date": "2026-01-15",
            "amount": "50.00",
            "category": "equipment",
            "description": "New arrows",
            "receipt_reference": "INV-001",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    txn = FinancialTransaction.query.filter_by(description="New arrows").first()
    assert txn is not None
    assert txn.type == "expense"
    assert txn.amount_cents == 5000
    assert txn.receipt_reference == "INV-001"


def test_create_income_page(client, admin_user):
    """Test accessing create income page."""
    _login_admin(client, admin_user)
    response = client.get("/admin/finance/income/create")
    assert response.status_code == 200
    assert b"Add Income" in response.data


def test_create_income_success(client, admin_user, app):
    """Test successfully creating income."""
    _login_admin(client, admin_user)

    response = client.post(
        "/admin/finance/income/create",
        data={
            "date": "2026-01-20",
            "amount": "100.00",
            "category": "membership_fees",
            "description": "Annual membership",
            "source": "John Doe",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    txn = FinancialTransaction.query.filter_by(description="Annual membership").first()
    assert txn is not None
    assert txn.type == "income"
    assert txn.amount_cents == 10000
    assert txn.source == "John Doe"


def test_edit_transaction_page(client, admin_user, app):
    """Test accessing edit transaction page."""
    _login_admin(client, admin_user)
    txn = _create_expense(admin_user)

    response = client.get(f"/admin/finance/{txn.id}/edit")
    assert response.status_code == 200
    assert b"Edit Expense" in response.data


def test_edit_transaction_success(client, admin_user, app):
    """Test successfully editing a transaction."""
    _login_admin(client, admin_user)
    txn = _create_expense(admin_user)
    txn_id = txn.id

    response = client.post(
        f"/admin/finance/{txn_id}/edit",
        data={
            "date": "2026-02-01",
            "amount": "75.50",
            "category": "supplies",
            "description": "Updated expense",
            "receipt_reference": "REC-002",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    updated = db.session.get(FinancialTransaction, txn_id)
    assert updated.amount_cents == 7550
    assert updated.category == "supplies"
    assert updated.description == "Updated expense"


def test_edit_transaction_not_found(client, admin_user):
    """Test editing non-existent transaction."""
    _login_admin(client, admin_user)
    response = client.get("/admin/finance/99999/edit")
    assert response.status_code == 404


def test_delete_transaction(client, admin_user, app):
    """Test deleting a transaction."""
    _login_admin(client, admin_user)
    txn = _create_expense(admin_user)
    txn_id = txn.id

    response = client.post(
        f"/admin/finance/{txn_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert db.session.get(FinancialTransaction, txn_id) is None


def test_delete_transaction_not_found(client, admin_user):
    """Test deleting non-existent transaction."""
    _login_admin(client, admin_user)
    response = client.post(
        "/admin/finance/99999/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_financial_statement_page(client, admin_user):
    """Test accessing financial statement page."""
    _login_admin(client, admin_user)
    response = client.get("/admin/finance/statement")
    assert response.status_code == 200
    assert b"Financial Statement" in response.data


def test_financial_statement_generate(client, admin_user, app):
    """Test generating a financial statement."""
    _login_admin(client, admin_user)
    _create_expense(admin_user)
    _create_income(admin_user)

    response = client.post(
        "/admin/finance/statement",
        data={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        },
    )

    assert response.status_code == 200
    assert b"Total Income" in response.data
    assert b"Total Expenses" in response.data
    assert b"Net Balance" in response.data


def test_financial_statement_end_before_start(client, admin_user):
    """Test statement with end date before start date."""
    _login_admin(client, admin_user)

    response = client.post(
        "/admin/finance/statement",
        data={
            "start_date": "2026-02-01",
            "end_date": "2026-01-01",
        },
    )

    assert response.status_code == 200
    assert b"End date must be after start date" in response.data


def test_finance_requires_admin(client, test_user):
    """Test that finance routes require admin permissions."""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/finance")
    assert response.status_code in [302, 403]


def test_create_expense_requires_permission(client, test_user):
    """Test that expense creation requires permission."""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/finance/expense/create")
    assert response.status_code in [302, 403]


def test_financial_statement_requires_permission(client, test_user):
    """Test that statement requires permission."""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/finance/statement")
    assert response.status_code in [302, 403]


def test_financial_statement_pdf_download(client, admin_user, app):
    """Test downloading a financial statement as PDF."""
    _login_admin(client, admin_user)
    _create_expense(admin_user)
    _create_income(admin_user)

    response = client.get("/admin/finance/statement/pdf?start_date=2026-01-01&end_date=2026-01-31")

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert b"attachment" in response.headers.get("Content-Disposition", "").encode()
    assert b"financial_statement_2026-01-01_to_2026-01-31.pdf" in response.headers.get("Content-Disposition", "").encode()
    # PDF files start with %PDF
    assert response.data[:5] == b"%PDF-"


def test_financial_statement_pdf_empty(client, admin_user, app):
    """Test downloading a PDF with no transactions in range."""
    _login_admin(client, admin_user)

    response = client.get("/admin/finance/statement/pdf?start_date=2026-06-01&end_date=2026-06-30")

    assert response.status_code == 200
    assert response.content_type == "application/pdf"
    assert response.data[:5] == b"%PDF-"


def test_financial_statement_pdf_missing_dates(client, admin_user):
    """Test PDF download with missing date parameters."""
    _login_admin(client, admin_user)

    response = client.get("/admin/finance/statement/pdf", follow_redirects=True)

    assert response.status_code == 200
    assert b"Please provide start and end dates" in response.data


def test_financial_statement_pdf_invalid_dates(client, admin_user):
    """Test PDF download with invalid date format."""
    _login_admin(client, admin_user)

    response = client.get("/admin/finance/statement/pdf?start_date=bad&end_date=worse", follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid date format" in response.data


def test_financial_statement_pdf_end_before_start(client, admin_user):
    """Test PDF download with end date before start date."""
    _login_admin(client, admin_user)

    response = client.get(
        "/admin/finance/statement/pdf?start_date=2026-02-01&end_date=2026-01-01",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"End date must be after start date" in response.data


def test_financial_statement_pdf_requires_permission(client, test_user):
    """Test that PDF download requires permission."""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/finance/statement/pdf?start_date=2026-01-01&end_date=2026-01-31")
    assert response.status_code in [302, 403]
