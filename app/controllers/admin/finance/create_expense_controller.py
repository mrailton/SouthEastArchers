from flask import render_template

from app.forms import ExpenseForm
from app.utils import permission_required


class CreateExpenseController:
    @permission_required("finance.create")
    def __call__(self):
        return render_template("admin/create_expense.html", form=ExpenseForm())
