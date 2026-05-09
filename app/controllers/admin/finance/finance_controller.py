from flask import render_template, request

from app.services import FinanceService
from app.utils import permission_required


class FinanceController:
    def __init__(self):
        super().__init__()
        self.service = FinanceService

    @permission_required("finance.read")
    def __call__(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        if per_page not in (5, 10, 20, 50, 100):
            per_page = 10
        pagination = self.service.get_all_transactions_paginated(page=page, per_page=per_page)
        return render_template("admin/finance.html", transactions=pagination.items, pagination=pagination, per_page=per_page)
