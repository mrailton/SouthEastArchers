"""Tests for FinanceService."""

from datetime import date

from app.services import FinanceService


def test_create_expense(app, admin_user):
    """Test creating an expense transaction."""
    txn, error = FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount=50.00,
        category="equipment",
        description="New target faces",
        created_by_id=admin_user.id,
        receipt_reference="INV-001",
    )

    assert error is None
    assert txn is not None
    assert txn.type == "expense"
    assert txn.amount == 50.00
    assert txn.amount_cents == 5000
    assert txn.category == "equipment"
    assert txn.receipt_reference == "INV-001"


def test_create_income(app, admin_user):
    """Test creating an income transaction."""
    txn, error = FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 20),
        amount=100.00,
        category="membership_fees",
        description="Annual membership - John Doe",
        created_by_id=admin_user.id,
        source="John Doe",
    )

    assert error is None
    assert txn is not None
    assert txn.type == "income"
    assert txn.amount == 100.00
    assert txn.amount_cents == 10000
    assert txn.source == "John Doe"


def test_update_transaction(app, admin_user):
    """Test updating a transaction."""
    txn, _ = FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount=50.00,
        category="equipment",
        description="New target faces",
        created_by_id=admin_user.id,
    )

    success, error = FinanceService.update_transaction(
        transaction=txn,
        txn_date=date(2026, 1, 16),
        amount=75.50,
        category="supplies",
        description="Updated description",
        receipt_reference="REC-002",
    )

    assert success is True
    assert error is None
    assert txn.amount == 75.50
    assert txn.category == "supplies"
    assert txn.date == date(2026, 1, 16)


def test_delete_transaction(app, admin_user):
    """Test deleting a transaction."""
    txn, _ = FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount=50.00,
        category="equipment",
        description="To delete",
        created_by_id=admin_user.id,
    )
    txn_id = txn.id

    success, error = FinanceService.delete_transaction(txn_id)

    assert success is True
    assert error is None
    assert FinanceService.get_transaction_by_id(txn_id) is None


def test_delete_transaction_not_found(app):
    """Test deleting a non-existent transaction."""
    success, error = FinanceService.delete_transaction(99999)

    assert success is False
    assert error == "Transaction not found"


def test_get_all_transactions(app, admin_user):
    """Test getting all transactions."""
    FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount=50.00,
        category="equipment",
        description="Expense 1",
        created_by_id=admin_user.id,
    )
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 20),
        amount=100.00,
        category="donations",
        description="Income 1",
        created_by_id=admin_user.id,
    )

    transactions = FinanceService.get_all_transactions()
    assert len(transactions) == 2


def test_get_expenses(app, admin_user):
    """Test getting only expenses."""
    FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount=50.00,
        category="equipment",
        description="Expense",
        created_by_id=admin_user.id,
    )
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 20),
        amount=100.00,
        category="donations",
        description="Income",
        created_by_id=admin_user.id,
    )

    expenses = FinanceService.get_expenses()
    assert len(expenses) == 1
    assert expenses[0].type == "expense"


def test_get_income(app, admin_user):
    """Test getting only income."""
    FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount=50.00,
        category="equipment",
        description="Expense",
        created_by_id=admin_user.id,
    )
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 20),
        amount=100.00,
        category="donations",
        description="Income",
        created_by_id=admin_user.id,
    )

    income = FinanceService.get_income()
    assert len(income) == 1
    assert income[0].type == "income"


def test_generate_statement(app, admin_user):
    """Test generating a financial statement for a date range."""
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 10),
        amount=200.00,
        category="membership_fees",
        description="Membership fee",
        created_by_id=admin_user.id,
    )
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 20),
        amount=150.00,
        category="shoot_fees",
        description="Shoot fees collected",
        created_by_id=admin_user.id,
    )
    FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount=75.00,
        category="venue_hire",
        description="Hall hire January",
        created_by_id=admin_user.id,
    )
    # Outside the range
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 2, 15),
        amount=500.00,
        category="donations",
        description="Should not appear",
        created_by_id=admin_user.id,
    )

    statement = FinanceService.generate_statement(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    assert len(statement["income_items"]) == 2
    assert len(statement["expense_items"]) == 1
    assert statement["total_income"] == 350.00
    assert statement["total_expenses"] == 75.00
    assert statement["net"] == 275.00
    assert statement["start_date"] == date(2026, 1, 1)
    assert statement["end_date"] == date(2026, 1, 31)


def test_generate_statement_empty_range(app, admin_user):
    """Test generating a statement with no transactions in range."""
    statement = FinanceService.generate_statement(
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
    )

    assert len(statement["income_items"]) == 0
    assert len(statement["expense_items"]) == 0
    assert statement["total_income"] == 0.0
    assert statement["total_expenses"] == 0.0
    assert statement["net"] == 0.0


def test_amount_property_rounding(app, admin_user):
    """Test that amount cents conversion handles rounding properly."""
    txn, _ = FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount=19.99,
        category="supplies",
        description="Test rounding",
        created_by_id=admin_user.id,
    )

    assert txn.amount_cents == 1999
    assert txn.amount == 19.99
