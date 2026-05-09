from app.controllers.admin.finance import (
    CreateExpenseController,
    CreateExpensePostController,
    CreateIncomeController,
    CreateIncomePostController,
    DeleteTransactionController,
    EditTransactionController,
    EditTransactionPostController,
    FinanceController,
    FinancialStatementController,
    FinancialStatementPdfController,
    FinancialStatementPostController,
)

from . import bp

bp.add_url_rule("/finance", view_func=FinanceController(), endpoint="finance", methods=["GET"])
bp.add_url_rule("/finance/expense/create", view_func=CreateExpenseController(), endpoint="create_expense", methods=["GET"])
bp.add_url_rule("/finance/expense/create", view_func=CreateExpensePostController(), endpoint="create_expense_post", methods=["POST"])
bp.add_url_rule("/finance/income/create", view_func=CreateIncomeController(), endpoint="create_income", methods=["GET"])
bp.add_url_rule("/finance/income/create", view_func=CreateIncomePostController(), endpoint="create_income_post", methods=["POST"])
bp.add_url_rule("/finance/<int:transaction_id>/edit", view_func=EditTransactionController(), endpoint="edit_transaction", methods=["GET"])
bp.add_url_rule("/finance/<int:transaction_id>/edit", view_func=EditTransactionPostController(), endpoint="edit_transaction_post", methods=["POST"])
bp.add_url_rule("/finance/<int:transaction_id>/delete", view_func=DeleteTransactionController(), endpoint="delete_transaction", methods=["POST"])
bp.add_url_rule("/finance/statement", view_func=FinancialStatementController(), endpoint="financial_statement", methods=["GET"])
bp.add_url_rule("/finance/statement", view_func=FinancialStatementPostController(), endpoint="financial_statement_post", methods=["POST"])
bp.add_url_rule("/finance/statement/pdf", view_func=FinancialStatementPdfController(), endpoint="financial_statement_pdf", methods=["GET"])
