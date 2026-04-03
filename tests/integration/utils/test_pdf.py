from datetime import date

from app.services import FinanceService
from app.utils.pdf import generate_statement_pdf


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

    pdf_bytes = generate_statement_pdf(statement)

    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:5] == b"%PDF-"


def test_generate_statement_pdf_empty(app, admin_user):
    """Test generating a PDF with no transactions."""
    statement = FinanceService.generate_statement(
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
    )

    pdf_bytes = generate_statement_pdf(statement)

    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert pdf_bytes[:5] == b"%PDF-"
