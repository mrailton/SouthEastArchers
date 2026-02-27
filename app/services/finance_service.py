"""Service layer for financial transaction operations."""

from __future__ import annotations

from datetime import date

from app.models import FinancialTransaction
from app.repositories import FinancialTransactionRepository


class FinanceService:
    @staticmethod
    def create_transaction(
        txn_type: str,
        txn_date: date,
        amount: float,
        category: str,
        description: str,
        created_by_id: int,
        source: str | None = None,
        receipt_reference: str | None = None,
    ) -> tuple[FinancialTransaction | None, str | None]:
        """Create a new financial transaction (income or expense)."""
        transaction = FinancialTransaction(
            type=txn_type,
            date=txn_date,
            category=category,
            description=description,
            created_by_id=created_by_id,
            source=source,
            receipt_reference=receipt_reference,
        )
        transaction.amount = amount

        try:
            FinancialTransactionRepository.add(transaction)
            FinancialTransactionRepository.save()
            return transaction, None
        except Exception as e:
            return None, f"Error creating transaction: {str(e)}"

    @staticmethod
    def update_transaction(
        transaction: FinancialTransaction,
        txn_date: date,
        amount: float,
        category: str,
        description: str,
        source: str | None = None,
        receipt_reference: str | None = None,
    ) -> tuple[bool, str | None]:
        """Update an existing financial transaction."""
        transaction.date = txn_date
        transaction.category = category
        transaction.description = description
        transaction.source = source
        transaction.receipt_reference = receipt_reference
        transaction.amount = amount

        try:
            FinancialTransactionRepository.save()
            return True, None
        except Exception as e:
            return False, f"Error updating transaction: {str(e)}"

    @staticmethod
    def delete_transaction(transaction_id: int) -> tuple[bool, str | None]:
        """Delete a financial transaction by ID."""
        transaction = FinancialTransactionRepository.get_by_id(transaction_id)
        if not transaction:
            return False, "Transaction not found"

        try:
            FinancialTransactionRepository.delete(transaction)
            FinancialTransactionRepository.save()
            return True, None
        except Exception as e:
            return False, f"Error deleting transaction: {str(e)}"

    @staticmethod
    def get_transaction_by_id(transaction_id: int) -> FinancialTransaction | None:
        """Get a financial transaction by ID."""
        return FinancialTransactionRepository.get_by_id(transaction_id)

    @staticmethod
    def get_all_transactions() -> list[FinancialTransaction]:
        """Get all financial transactions ordered by date descending."""
        return FinancialTransactionRepository.get_all()

    @staticmethod
    def get_expenses() -> list[FinancialTransaction]:
        """Get all expense transactions."""
        return FinancialTransactionRepository.get_by_type("expense")

    @staticmethod
    def get_income() -> list[FinancialTransaction]:
        """Get all income transactions."""
        return FinancialTransactionRepository.get_by_type("income")

    @staticmethod
    def generate_statement(
        start_date: date,
        end_date: date,
    ) -> dict:
        """Generate a financial statement for a date range.

        Returns a dict with income items, expense items, totals, and net balance.
        """
        income_items = FinancialTransactionRepository.get_by_date_range(start_date, end_date, txn_type="income")
        expense_items = FinancialTransactionRepository.get_by_date_range(start_date, end_date, txn_type="expense")

        total_income_cents = sum(item.amount_cents for item in income_items)
        total_expenses_cents = sum(item.amount_cents for item in expense_items)
        net_cents = total_income_cents - total_expenses_cents

        return {
            "income_items": income_items,
            "expense_items": expense_items,
            "total_income_cents": total_income_cents,
            "total_expenses_cents": total_expenses_cents,
            "net_cents": net_cents,
            "total_income": total_income_cents / 100.0,
            "total_expenses": total_expenses_cents / 100.0,
            "net": net_cents / 100.0,
            "start_date": start_date,
            "end_date": end_date,
        }

    @staticmethod
    def generate_statement_pdf(statement: dict) -> bytes:
        """Generate a PDF of a financial statement and return it as bytes."""
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # --- Title ---
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, "South East Archers", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Financial Statement", new_x="LMARGIN", new_y="NEXT", align="C")

        # --- Period ---
        pdf.set_font("Helvetica", "", 10)
        period = f"{statement['start_date'].strftime('%d %B %Y')} - {statement['end_date'].strftime('%d %B %Y')}"
        pdf.cell(0, 8, period, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(6)

        # --- Summary box ---
        eur = "EUR "
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(63, 8, f"Total Income:  {eur}{statement['total_income']:.2f}", border=1, fill=True)
        pdf.cell(63, 8, f"Total Expenses:  {eur}{statement['total_expenses']:.2f}", border=1, fill=True)
        net = statement["net"]
        net_label = f"Net Balance:  {eur}{abs(net):.2f}" if net >= 0 else f"Net Balance:  -{eur}{abs(net):.2f}"
        pdf.cell(64, 8, net_label, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        col_date_w = 28
        col_cat_w = 40
        col_desc_w = 82
        col_amt_w = 40

        def _render_table(title: str, items: list, color: tuple) -> None:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*color)
            pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)

            if not items:
                pdf.set_font("Helvetica", "I", 10)
                pdf.cell(0, 8, f"No {title.lower()} recorded for this period.", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(4)
                return

            # Table header
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(col_date_w, 7, "Date", border=1, fill=True)
            pdf.cell(col_cat_w, 7, "Category", border=1, fill=True)
            pdf.cell(col_desc_w, 7, "Description", border=1, fill=True)
            pdf.cell(col_amt_w, 7, "Amount", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

            # Table rows
            pdf.set_font("Helvetica", "", 9)
            total_cents = 0
            for item in items:
                total_cents += item.amount_cents
                category_label = item.category.replace("_", " ").title()
                desc = item.description[:45] + "..." if len(item.description) > 48 else item.description
                pdf.cell(col_date_w, 7, item.date.strftime("%Y-%m-%d"), border=1)
                pdf.cell(col_cat_w, 7, category_label, border=1)
                pdf.cell(col_desc_w, 7, desc, border=1)
                pdf.cell(col_amt_w, 7, f"{eur}{item.amount:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")

            # Total row
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(col_date_w + col_cat_w + col_desc_w, 7, "Total", border=1)
            pdf.cell(col_amt_w, 7, f"{eur}{total_cents / 100:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)

        # --- Income table ---
        _render_table("Income", statement["income_items"], (0, 128, 0))

        # --- Expenses table ---
        _render_table("Expenses", statement["expense_items"], (192, 0, 0))

        # --- Footer ---
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(128, 128, 128)
        generated = date.today().strftime("%d %B %Y")
        pdf.cell(0, 6, f"Generated on {generated} | South East Archers", align="C")

        return pdf.output()
