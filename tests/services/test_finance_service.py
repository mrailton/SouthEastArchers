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


def test_generate_statement_pdf(app, admin_user):
    """Test generating a PDF from a financial statement."""
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 10),
        amount=200.00,
        category="membership_fees",
        description="Membership fee",
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

    statement = FinanceService.generate_statement(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    pdf_bytes = FinanceService.generate_statement_pdf(statement)

    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:5] == b"%PDF-"


def test_generate_statement_pdf_empty(app, admin_user):
    """Test generating a PDF with no transactions."""
    statement = FinanceService.generate_statement(
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
    )

    pdf_bytes = FinanceService.generate_statement_pdf(statement)

    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert pdf_bytes[:5] == b"%PDF-"


def test_record_sumup_payment_transactions_creates_income_and_expense(app, admin_user):
    """Test that record_sumup_payment_transactions creates both income and fee expense."""
    from decimal import Decimal

    from app.services.settings_service import SettingsService

    settings = SettingsService.get()
    settings.sumup_fee_percentage = Decimal("2.50")
    SettingsService.save(settings)

    success, error = FinanceService.record_sumup_payment_transactions(
        payment_amount_cents=10000,
        payment_type="membership",
        description="Annual membership - Test User",
        created_by_id=admin_user.id,
        receipt_reference="txn_abc123",
    )

    assert success is True
    assert error is None

    transactions = FinanceService.get_all_transactions()
    assert len(transactions) == 2

    income = [t for t in transactions if t.type == "income"][0]
    assert income.amount == 100.00
    assert income.category == "membership_fees"
    assert income.source == "SumUp"
    assert income.receipt_reference == "txn_abc123"

    expense = [t for t in transactions if t.type == "expense"][0]
    assert expense.amount == 2.50
    assert expense.category == "payment_processing_fees"
    assert "SumUp fee (2.5%)" in expense.description
    assert expense.receipt_reference == "txn_abc123"


def test_record_sumup_payment_transactions_credit_purchase(app, admin_user):
    """Test that credit purchases use shoot_fees category."""
    from decimal import Decimal

    from app.services.settings_service import SettingsService

    settings = SettingsService.get()
    settings.sumup_fee_percentage = Decimal("2.50")
    SettingsService.save(settings)

    success, error = FinanceService.record_sumup_payment_transactions(
        payment_amount_cents=500,
        payment_type="credits",
        description="1 shooting credit",
        created_by_id=admin_user.id,
    )

    assert success is True
    income = [t for t in FinanceService.get_all_transactions() if t.type == "income"][0]
    assert income.category == "shoot_fees"
    assert income.amount == 5.00


def test_record_sumup_payment_transactions_skips_when_no_fee_configured(app, admin_user):
    """Test that it gracefully skips when sumup_fee_percentage is not set."""
    from app.services.settings_service import SettingsService

    settings = SettingsService.get()
    settings.sumup_fee_percentage = None
    SettingsService.save(settings)

    success, error = FinanceService.record_sumup_payment_transactions(
        payment_amount_cents=10000,
        payment_type="membership",
        description="Test",
        created_by_id=admin_user.id,
    )

    assert success is False
    assert "not configured" in error
    assert len(FinanceService.get_all_transactions()) == 0


def test_record_cash_payment_transaction_creates_income(app, admin_user):
    """Test that record_cash_payment_transaction creates an income transaction."""
    success, error = FinanceService.record_cash_payment_transaction(
        payment_amount_cents=10000,
        payment_type="membership",
        description="Annual membership (Cash)",
        created_by_id=admin_user.id,
    )

    assert success is True
    assert error is None

    transactions = FinanceService.get_all_transactions()
    assert len(transactions) == 1

    income = transactions[0]
    assert income.type == "income"
    assert income.amount == 100.00
    assert income.category == "membership_fees"
    assert income.source == "Cash"
    assert income.description == "Annual membership (Cash)"


def test_record_cash_payment_transaction_credit_purchase(app, admin_user):
    """Test that cash credit purchases use shoot_fees category."""
    success, error = FinanceService.record_cash_payment_transaction(
        payment_amount_cents=500,
        payment_type="credits",
        description="1 shooting credit (Cash)",
        created_by_id=admin_user.id,
    )

    assert success is True
    income = FinanceService.get_all_transactions()[0]
    assert income.category == "shoot_fees"
    assert income.amount == 5.00
    assert income.source == "Cash"
