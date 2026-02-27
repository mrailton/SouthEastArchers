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
