from datetime import date

from app.models import FinancialTransaction
from app.services import FinanceService


def test_create_expense(app, admin_user):
    """Test creating an expense transaction."""
    result = FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount_cents=5000,
        category="equipment",
        description="New target faces",
        created_by_id=admin_user.id,
        receipt_reference="INV-001",
    )

    assert result.success is True
    assert result.data is not None
    assert result.data.type == "expense"
    assert result.data.amount == 50.00
    assert result.data.amount_cents == 5000
    assert result.data.category == "equipment"
    assert result.data.receipt_reference == "INV-001"


def test_create_income(app, admin_user):
    """Test creating an income transaction."""
    result = FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 20),
        amount_cents=10000,
        category="membership_fees",
        description="Annual membership - John Doe",
        created_by_id=admin_user.id,
        source="John Doe",
    )

    assert result.success is True
    assert result.data is not None
    assert result.data.type == "income"
    assert result.data.amount == 100.00
    assert result.data.amount_cents == 10000
    assert result.data.source == "John Doe"


def test_update_transaction(app, admin_user):
    """Test updating a transaction."""
    result = FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount_cents=5000,
        category="equipment",
        description="New target faces",
        created_by_id=admin_user.id,
    )
    txn = result.data

    result = FinanceService.update_transaction(
        transaction=txn,
        txn_date=date(2026, 1, 16),
        amount_cents=7550,
        category="supplies",
        description="Updated description",
        receipt_reference="REC-002",
    )

    assert result.success is True
    assert txn.amount == 75.50
    assert txn.category == "supplies"
    assert txn.date == date(2026, 1, 16)


def test_delete_transaction(app, admin_user):
    """Test deleting a transaction."""
    result = FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount_cents=5000,
        category="equipment",
        description="To delete",
        created_by_id=admin_user.id,
    )
    txn_id = result.data.id

    result = FinanceService.delete_transaction(txn_id)

    assert result.success is True
    assert FinanceService.get_transaction_by_id(txn_id) is None


def test_delete_transaction_not_found(app):
    """Test deleting a non-existent transaction."""
    result = FinanceService.delete_transaction(99999)

    assert result.success is False
    assert result.message == "Transaction not found"


def test_generate_statement(app, admin_user):
    """Test generating a financial statement for a date range."""
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 10),
        amount_cents=20000,
        category="membership_fees",
        description="Membership fee",
        created_by_id=admin_user.id,
    )
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 20),
        amount_cents=15000,
        category="shoot_fees",
        description="Shoot fees collected",
        created_by_id=admin_user.id,
    )
    FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount_cents=7500,
        category="venue_hire",
        description="Hall hire January",
        created_by_id=admin_user.id,
    )
    # Outside the range
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 2, 15),
        amount_cents=50000,
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
    result = FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount_cents=1999,
        category="supplies",
        description="Test rounding",
        created_by_id=admin_user.id,
    )

    assert result.data.amount_cents == 1999
    assert result.data.amount == 19.99


def test_generate_statement_pdf(app, admin_user):
    """Test generating a PDF from a financial statement."""
    FinanceService.create_transaction(
        txn_type="income",
        txn_date=date(2026, 1, 10),
        amount_cents=20000,
        category="membership_fees",
        description="Membership fee",
        created_by_id=admin_user.id,
    )
    FinanceService.create_transaction(
        txn_type="expense",
        txn_date=date(2026, 1, 15),
        amount_cents=7500,
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

    SettingsService.set("sumup_fee_percentage", Decimal("2.50"))

    result = FinanceService.record_sumup_payment_transactions(
        payment_amount_cents=10000,
        payment_type="membership",
        description="Annual membership - Test User",
        created_by_id=admin_user.id,
        receipt_reference="txn_abc123",
    )

    assert result.success is True

    transactions = FinancialTransaction.query.all()
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

    SettingsService.set("sumup_fee_percentage", Decimal("2.50"))

    result = FinanceService.record_sumup_payment_transactions(
        payment_amount_cents=500,
        payment_type="credits",
        description="1 shooting credit",
        created_by_id=admin_user.id,
    )

    assert result.success is True
    income = [t for t in FinancialTransaction.query.all() if t.type == "income"][0]
    assert income.category == "shoot_fees"
    assert income.amount == 5.00


def test_record_sumup_payment_transactions_skips_when_no_fee_configured(app, admin_user):
    """Test that it gracefully skips when sumup_fee_percentage is not set."""
    # Default is None, so no need to set explicitly

    result = FinanceService.record_sumup_payment_transactions(
        payment_amount_cents=10000,
        payment_type="membership",
        description="Test",
        created_by_id=admin_user.id,
    )

    assert result.success is False
    assert "not configured" in result.message
    assert len(FinancialTransaction.query.all()) == 0


def test_record_cash_payment_transaction_creates_income(app, admin_user):
    """Test that record_cash_payment_transaction creates an income transaction."""
    result = FinanceService.record_cash_payment_transaction(
        payment_amount_cents=10000,
        payment_type="membership",
        description="Annual membership (Cash)",
        created_by_id=admin_user.id,
    )

    assert result.success is True

    transactions = FinancialTransaction.query.all()
    assert len(transactions) == 1

    income = transactions[0]
    assert income.type == "income"
    assert income.amount == 100.00
    assert income.category == "membership_fees"
    assert income.source == "Cash"
    assert income.description == "Annual membership (Cash)"


def test_record_cash_payment_transaction_credit_purchase(app, admin_user):
    """Test that cash credit purchases use shoot_fees category."""
    result = FinanceService.record_cash_payment_transaction(
        payment_amount_cents=500,
        payment_type="credits",
        description="1 shooting credit (Cash)",
        created_by_id=admin_user.id,
    )

    assert result.success is True
    income = FinancialTransaction.query.all()[0]
    assert income.category == "shoot_fees"
    assert income.amount == 5.00
    assert income.source == "Cash"
