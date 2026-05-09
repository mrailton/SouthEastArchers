from flask import render_template, request

from app.services import ShootService
from app.utils import permission_required


class ShootsController:
    def __init__(self):
        super().__init__()
        self.service = ShootService

    @permission_required("shoots.read")
    def __call__(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        if per_page not in (5, 10, 20, 50, 100):
            per_page = 10
        pagination = self.service.get_all_shoots_paginated(page=page, per_page=per_page)
        return render_template("admin/shoots.html", shoots=pagination.items, pagination=pagination, per_page=per_page)
