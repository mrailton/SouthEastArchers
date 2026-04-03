from __future__ import annotations

from datetime import date

from flask_sqlalchemy.pagination import Pagination

from app.enums import PaymentType
from app.models import FinancialTransaction
from app.repositories import FinancialTransactionRepository
from app.services.result import ServiceResult


class FinanceService:
    @staticmethod
    def create_transaction(
        txn_type: str,
        txn_date: date,
        amount_cents: int,
        category: str,
        description: str,
        created_by_id: int,
        source: str | None = None,
        receipt_reference: str | None = None,
    ) -> ServiceResult[FinancialTransaction]:
        """Create a new financial transaction (income or expense)."""
        transaction = FinancialTransaction(
            type=txn_type,
            date=txn_date,
            amount_cents=amount_cents,
            category=category,
            description=description,
            created_by_id=created_by_id,
            source=source,
            receipt_reference=receipt_reference,
        )

        try:
            FinancialTransactionRepository.add(transaction)
            FinancialTransactionRepository.save()
            return ServiceResult.ok(data=transaction)
        except Exception as e:
            return ServiceResult.fail(f"Error creating transaction: {str(e)}")

    @staticmethod
    def record_sumup_payment_transactions(
        payment_amount_cents: int,
        payment_type: str,
        description: str,
        created_by_id: int,
        receipt_reference: str | None = None,
    ) -> ServiceResult[None]:
        """Record income and SumUp fee expense for a completed online payment.

        Creates two financial transactions:
        1. Income for the full payment amount
        2. Expense for the SumUp processing fee (based on sumup_fee_percentage setting)
        """
        from flask import current_app

        from app.services.settings_service import SettingsService

        fee_pct = SettingsService.get("sumup_fee_percentage")
        if fee_pct is None:
            current_app.logger.warning("SumUp fee percentage not configured in settings — skipping automatic financial transaction recording")
            return ServiceResult.fail("SumUp fee percentage not configured")

        fee_pct = float(fee_pct)
        today = date.today()
        fee_amount_cents = int(round(payment_amount_cents * fee_pct / 100.0))

        # Determine income category based on payment type
        category = "membership_fees" if payment_type == PaymentType.MEMBERSHIP else "shoot_fees"

        # 1. Record the income
        result = FinanceService.create_transaction(
            txn_type="income",
            txn_date=today,
            amount_cents=payment_amount_cents,
            category=category,
            description=description,
            created_by_id=created_by_id,
            source="SumUp",
            receipt_reference=receipt_reference,
        )
        if not result.success:
            return ServiceResult.fail(f"Error recording income: {result.message}")

        # 2. Record the SumUp fee as an expense
        result = FinanceService.create_transaction(
            txn_type="expense",
            txn_date=today,
            amount_cents=fee_amount_cents,
            category="payment_processing_fees",
            description=f"SumUp fee ({fee_pct}%) on {description}",
            created_by_id=created_by_id,
            receipt_reference=receipt_reference,
        )
        if not result.success:
            return ServiceResult.fail(f"Error recording SumUp fee: {result.message}")

        return ServiceResult.ok()

    @staticmethod
    def record_cash_payment_transaction(
        payment_amount_cents: int,
        payment_type: str,
        description: str,
        created_by_id: int,
    ) -> ServiceResult[None]:
        """Record an income transaction for a completed cash payment."""
        today = date.today()
        category = "membership_fees" if payment_type == PaymentType.MEMBERSHIP else "shoot_fees"

        result = FinanceService.create_transaction(
            txn_type="income",
            txn_date=today,
            amount_cents=payment_amount_cents,
            category=category,
            description=description,
            created_by_id=created_by_id,
            source="Cash",
        )
        if not result.success:
            return ServiceResult.fail(f"Error recording income: {result.message}")

        return ServiceResult.ok()

    @staticmethod
    def update_transaction(
        transaction: FinancialTransaction,
        txn_date: date,
        amount_cents: int,
        category: str,
        description: str,
        source: str | None = None,
        receipt_reference: str | None = None,
    ) -> ServiceResult[None]:
        """Update an existing financial transaction."""
        transaction.date = txn_date
        transaction.category = category
        transaction.description = description
        transaction.source = source
        transaction.receipt_reference = receipt_reference
        transaction.amount_cents = amount_cents

        try:
            FinancialTransactionRepository.save()
            return ServiceResult.ok()
        except Exception as e:
            return ServiceResult.fail(f"Error updating transaction: {str(e)}")

    @staticmethod
    def delete_transaction(transaction_id: int) -> ServiceResult[None]:
        """Delete a financial transaction by ID."""
        transaction = FinancialTransactionRepository.get_by_id(transaction_id)
        if not transaction:
            return ServiceResult.fail("Transaction not found")

        try:
            FinancialTransactionRepository.delete(transaction)
            FinancialTransactionRepository.save()
            return ServiceResult.ok()
        except Exception as e:
            return ServiceResult.fail(f"Error deleting transaction: {str(e)}")

    @staticmethod
    def get_transaction_by_id(transaction_id: int) -> FinancialTransaction | None:
        """Get a financial transaction by ID."""
        return FinancialTransactionRepository.get_by_id(transaction_id)

    @staticmethod
    def get_all_transactions_paginated(page: int = 1, per_page: int = 20) -> Pagination:
        """Get paginated financial transactions ordered by date descending."""
        return FinancialTransactionRepository.get_all_paginated(page=page, per_page=per_page)

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

        def _group_by_category(items: list[FinancialTransaction]) -> list[dict[str, object]]:
            groups: dict[str, dict] = {}
            for item in items:
                label = item.category.replace("_", " ").title()
                entry = groups.setdefault(item.category, {"label": label, "total_cents": 0, "count": 0})
                entry["total_cents"] += item.amount_cents
                entry["count"] += 1
            for entry in groups.values():
                entry["total"] = entry["total_cents"] / 100.0
            return sorted(groups.values(), key=lambda e: e["total_cents"], reverse=True)

        return {
            "income_items": income_items,
            "expense_items": expense_items,
            "income_by_category": _group_by_category(income_items),
            "expense_by_category": _group_by_category(expense_items),
            "total_income_cents": total_income_cents,
            "total_expenses_cents": total_expenses_cents,
            "net_cents": net_cents,
            "total_income": total_income_cents / 100.0,
            "total_expenses": total_expenses_cents / 100.0,
            "net": net_cents / 100.0,
            "start_date": start_date,
            "end_date": end_date,
        }
