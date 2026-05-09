from flask import flash, redirect, url_for

from app.services import FinanceService
from app.utils import permission_required


class DeleteTransactionController:
    def __init__(self):
        super().__init__()
        self.service = FinanceService

    @permission_required("finance.delete")
    def __call__(self, transaction_id):
        result = self.service.delete_transaction(transaction_id)

        if not result.success:
            flash(result.message or "An error occurred while deleting the transaction.", "error")
        else:
            flash("Transaction deleted successfully!", "success")

        return redirect(url_for("admin.finance"))
