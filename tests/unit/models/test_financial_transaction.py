from datetime import date

from app.models import FinancialTransaction


def test_create_income_transaction(app, test_user):
    """Test creating an income transaction"""
    from app import db

    transaction = FinancialTransaction(
        type="income",
        date=date.today(),
        amount_cents=5000,
        currency="EUR",
        category="membership_fees",
        description="Test membership fee",
        source="Test source",
        created_by_id=test_user.id,
    )
    db.session.add(transaction)
    db.session.commit()

    assert transaction.id is not None
    assert transaction.type == "income"
    assert transaction.amount == 50.0
    assert transaction.currency == "EUR"


def test_create_expense_transaction(app, test_user):
    """Test creating an expense transaction"""
    from app import db

    transaction = FinancialTransaction(
        type="expense",
        date=date.today(),
        amount_cents=2500,
        currency="EUR",
        category="equipment",
        description="Test equipment purchase",
        source="Supplier",
        created_by_id=test_user.id,
    )
    db.session.add(transaction)
    db.session.commit()

    assert transaction.id is not None
    assert transaction.type == "expense"
    assert transaction.amount == 25.0


def test_transaction_amount_property(app, test_user):
    """Test amount property converts cents to euros"""
    from app import db

    transaction = FinancialTransaction(
        type="income",
        date=date.today(),
        amount_cents=12345,
        currency="EUR",
        category="donations",
        description="Test",
        created_by_id=test_user.id,
    )
    db.session.add(transaction)
    db.session.commit()

    assert transaction.amount == 123.45


def test_transaction_repr(app, test_user):
    """Test financial transaction repr"""
    from app import db

    transaction = FinancialTransaction(
        type="income",
        date=date.today(),
        amount_cents=5000,
        currency="EUR",
        category="membership_fees",
        description="Test",
        created_by_id=test_user.id,
    )
    db.session.add(transaction)
    db.session.commit()

    repr_str = repr(transaction)
    assert "FinancialTransaction" in repr_str
    assert "income" in repr_str
    assert "50" in repr_str


def test_income_categories():
    """Test income categories list"""
    from app.models.financial_transaction import INCOME_CATEGORIES

    assert len(INCOME_CATEGORIES) > 0
    assert any(cat[0] == "membership_fees" for cat in INCOME_CATEGORIES)


def test_expense_categories():
    """Test expense categories list"""
    from app.models.financial_transaction import EXPENSE_CATEGORIES

    assert len(EXPENSE_CATEGORIES) > 0
    assert any(cat[0] == "equipment" for cat in EXPENSE_CATEGORIES)
