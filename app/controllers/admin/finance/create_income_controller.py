from flask import render_template

from app.forms import IncomeForm
from app.utils import permission_required


class CreateIncomeController:
    @permission_required("finance.create")
    def __call__(self):
        return render_template("admin/create_income.html", form=IncomeForm())
