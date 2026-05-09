from flask import flash, render_template

from app.forms import FinancialStatementForm
from app.services import FinanceService
from app.utils import permission_required


class FinancialStatementPostController:
    def __init__(self):
        super().__init__()
        self.service = FinanceService

    @permission_required("finance.report")
    def __call__(self):
        form = FinancialStatementForm()

        if form.validate_on_submit():
            if form.end_date.data < form.start_date.data:
                flash("End date must be after start date.", "error")
                return render_template("admin/financial_statement.html", form=form, statement=None)

            statement = self.service.generate_statement(
                start_date=form.start_date.data,
                end_date=form.end_date.data,
            )
            return render_template("admin/financial_statement.html", form=form, statement=statement)

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("admin/financial_statement.html", form=form, statement=None)
