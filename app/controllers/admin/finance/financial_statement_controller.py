from datetime import date

from flask import render_template

from app.forms import FinancialStatementForm
from app.utils import permission_required


class FinancialStatementController:
    @permission_required("finance.report")
    def __call__(self):
        today = date.today()
        current_year = today.year

        if today.month >= 3:
            start_date = date(current_year, 3, 1)
        else:
            start_date = date(current_year - 1, 3, 1)

        end_date = today

        form = FinancialStatementForm()
        form.start_date.data = start_date
        form.end_date.data = end_date

        return render_template("admin/financial_statement.html", form=form, statement=None)
