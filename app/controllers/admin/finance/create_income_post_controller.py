from flask import flash, redirect, render_template, url_for
from flask_login import current_user

from app.forms import IncomeForm
from app.services import FinanceService
from app.utils import permission_required


class CreateIncomePostController:
    def __init__(self):
        super().__init__()
        self.service = FinanceService

    @permission_required("finance.create")
    def __call__(self):
        form = IncomeForm()

        if form.validate_on_submit():
            result = self.service.create_transaction(
                txn_type="income",
                txn_date=form.date.data,
                amount_cents=int(round(float(form.amount.data) * 100)),
                category=form.category.data,
                description=form.description.data,
                created_by_id=current_user.id,
                source=form.source.data or None,
            )

            if not result.success:
                flash(result.message, "error")
                return render_template("admin/create_income.html", form=form)

            flash("Income recorded successfully!", "success")
            return redirect(url_for("admin.finance"))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("admin/create_income.html", form=form)
