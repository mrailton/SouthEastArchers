from flask import abort, flash, redirect, render_template, url_for

from app.forms import ExpenseForm, IncomeForm
from app.services import FinanceService
from app.utils import permission_required


class EditTransactionPostController:
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
        else:
            form = IncomeForm(obj=transaction)

        if form.validate_on_submit():
            kwargs = dict(
                transaction=transaction,
                txn_date=form.date.data,
                amount_cents=int(round(float(form.amount.data) * 100)),
                category=form.category.data,
                description=form.description.data,
            )
            if transaction.type == "expense":
                kwargs["receipt_reference"] = form.receipt_reference.data or None
            else:
                kwargs["source"] = form.source.data or None

            result = self.service.update_transaction(**kwargs)

            if not result.success:
                flash(result.message or "An error occurred while updating the transaction.", "error")
                return render_template(
                    "admin/edit_transaction.html",
                    transaction=transaction,
                    form=form,
                )

            flash("Transaction updated successfully!", "success")
            return redirect(url_for("admin.finance"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template(
            "admin/edit_transaction.html",
            transaction=transaction,
            form=form,
        )
