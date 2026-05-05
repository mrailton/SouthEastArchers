from flask import abort, render_template

from app.forms import ExpenseForm, IncomeForm
from app.services import FinanceService
from app.utils import permission_required


class EditTransactionController:
    def __init__(self):
        super().__init__()
        self.service = FinanceService

    @permission_required("finance.update")
    def __call__(self, transaction_id):
        transaction = self.service.get_transaction_by_id(transaction_id)
        if not transaction:
            abort(404)

        if transaction.type == "expense":
            form = ExpenseForm(obj=transaction)
            form.amount.data = transaction.amount
        else:
            form = IncomeForm(obj=transaction)
            form.amount.data = transaction.amount

        return render_template(
            "admin/edit_transaction.html",
            transaction=transaction,
            form=form,
        )
