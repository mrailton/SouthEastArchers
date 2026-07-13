from __future__ import annotations

import logging
from datetime import date

from app.db import Pagination
from app.enums import PaymentType
from app.models import FinancialTransaction
from app.repositories import BaseRepository, FinancialTransactionRepository
from app.services import settings
from app.services.result import ErrorCode, ServiceResult

logger = logging.getLogger(__name__)


def add_transaction(
    txn_type: str,
    txn_date: date,
    amount_cents: int,
    category: str,
    description: str,
    created_by_id: int,
    source: str | None = None,
    receipt_reference: str | None = None,
) -> ServiceResult[FinancialTransaction]:
    """Stage a transaction in the current unit of work (flush only, no commit)."""
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
        FinancialTransactionRepository.flush()
        return ServiceResult.ok(data=transaction)
    except Exception as exc:
        return ServiceResult.fail(f"Error creating transaction: {exc}")


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
    result = add_transaction(
        txn_type=txn_type,
        txn_date=txn_date,
        amount_cents=amount_cents,
        category=category,
        description=description,
        created_by_id=created_by_id,
        source=source,
        receipt_reference=receipt_reference,
    )
    if not result.success:
        return result

    try:
        FinancialTransactionRepository.save()
        return result
    except Exception as exc:
        return ServiceResult.fail(f"Error creating transaction: {exc}")


def _cash_receipt_reference(payment_id: int) -> str:
    return f"cash-payment-{payment_id}"


def _sumup_already_recorded(receipt_reference: str | None, category: str) -> bool:
    if not receipt_reference:
        return False
    return FinancialTransactionRepository.exists_for_receipt(receipt_reference, category, "income")


def _cash_already_recorded(payment_id: int, category: str) -> bool:
    return FinancialTransactionRepository.exists_for_receipt(_cash_receipt_reference(payment_id), category, "income")


def record_sumup_payment_transactions(
    payment_amount_cents: int,
    payment_type: str,
    description: str,
    created_by_id: int,
    receipt_reference: str | None = None,
) -> ServiceResult[None]:
    fee_pct = settings.get("sumup_fee_percentage")
    if fee_pct is None:
        logger.warning("SumUp fee percentage not configured in settings — skipping automatic financial transaction recording")
        return ServiceResult.fail("SumUp fee percentage not configured")

    fee_pct = float(fee_pct)
    today = date.today()
    fee_amount_cents = int(round(payment_amount_cents * fee_pct / 100.0))
    category = "membership_fees" if payment_type == PaymentType.MEMBERSHIP else "shoot_fees"

    if _sumup_already_recorded(receipt_reference, category):
        return ServiceResult.ok(message="Financial transactions already recorded.")

    try:
        with BaseRepository.transaction():
            income = add_transaction(
                txn_type="income",
                txn_date=today,
                amount_cents=payment_amount_cents,
                category=category,
                description=description,
                created_by_id=created_by_id,
                source="SumUp",
                receipt_reference=receipt_reference,
            )
            if not income.success:
                raise RuntimeError(income.message)

            expense = add_transaction(
                txn_type="expense",
                txn_date=today,
                amount_cents=fee_amount_cents,
                category="payment_processing_fees",
                description=f"SumUp fee ({fee_pct}%) on {description}",
                created_by_id=created_by_id,
                receipt_reference=receipt_reference,
            )
            if not expense.success:
                raise RuntimeError(expense.message)
        return ServiceResult.ok()
    except RuntimeError as exc:
        return ServiceResult.fail(str(exc))
    except Exception as exc:
        return ServiceResult.fail(f"Error recording SumUp payment transactions: {exc}")


def record_payment_transactions_for_completed_payment(payment_id: int, payment_type: str) -> ServiceResult[None]:
    """Record ledger entries for a completed payment (used by event handlers)."""
    from app.repositories import PaymentRepository

    payment = PaymentRepository.get_by_id_with_user(payment_id)
    if not payment:
        return ServiceResult.fail("Payment not found.", error_code=ErrorCode.NOT_FOUND)

    if payment.payment_processor == "sumup":
        return record_sumup_payment_transactions(
            payment_amount_cents=payment.amount_cents,
            payment_type=payment_type,
            description=payment.description or f"SumUp {payment_type} payment",
            created_by_id=payment.user_id,
            receipt_reference=payment.external_transaction_id,
        )
    if payment.payment_processor == "cash":
        return record_cash_payment_transaction(
            payment_amount_cents=payment.amount_cents,
            payment_type=payment_type,
            description=payment.description or f"Cash {payment_type} payment",
            created_by_id=payment.user_id,
            payment_id=payment.id,
        )
    return ServiceResult.ok()


def record_cash_payment_transaction(
    payment_amount_cents: int,
    payment_type: str,
    description: str,
    created_by_id: int,
    *,
    payment_id: int | None = None,
) -> ServiceResult[None]:
    today = date.today()
    category = "membership_fees" if payment_type == PaymentType.MEMBERSHIP else "shoot_fees"

    if payment_id is not None and _cash_already_recorded(payment_id, category):
        return ServiceResult.ok(message="Financial transactions already recorded.")

    receipt_reference = _cash_receipt_reference(payment_id) if payment_id is not None else None
    result = create_transaction(
        txn_type="income",
        txn_date=today,
        amount_cents=payment_amount_cents,
        category=category,
        description=description,
        created_by_id=created_by_id,
        source="Cash",
        receipt_reference=receipt_reference,
    )
    if not result.success:
        return ServiceResult.fail(f"Error recording income: {result.message}")

    return ServiceResult.ok()


def update_transaction(
    transaction: FinancialTransaction,
    txn_date: date,
    amount_cents: int,
    category: str,
    description: str,
    source: str | None = None,
    receipt_reference: str | None = None,
) -> ServiceResult[None]:
    transaction.date = txn_date
    transaction.category = category
    transaction.description = description
    transaction.source = source
    transaction.receipt_reference = receipt_reference
    transaction.amount_cents = amount_cents

    try:
        FinancialTransactionRepository.save()
        return ServiceResult.ok()
    except Exception as exc:
        return ServiceResult.fail(f"Error updating transaction: {exc}")


def delete_transaction(transaction_id: int) -> ServiceResult[None]:
    transaction = FinancialTransactionRepository.get_by_id(transaction_id)
    if not transaction:
        return ServiceResult.fail("Transaction not found", error_code=ErrorCode.NOT_FOUND)

    try:
        FinancialTransactionRepository.delete(transaction)
        FinancialTransactionRepository.save()
        return ServiceResult.ok()
    except Exception as exc:
        return ServiceResult.fail(f"Error deleting transaction: {exc}")


def get_transaction_by_id(transaction_id: int) -> FinancialTransaction | None:
    return FinancialTransactionRepository.get_by_id(transaction_id)


def get_all_transactions_paginated(page: int = 1, per_page: int = 20) -> Pagination:
    return FinancialTransactionRepository.get_all_paginated(page=page, per_page=per_page)


def generate_statement(start_date: date, end_date: date) -> dict:
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
