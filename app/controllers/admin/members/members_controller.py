from flask import render_template, request

from app.services import UserService
from app.utils import permission_required


class MembersController:
    def __init__(self):
        super().__init__()
        self.service = UserService

    @permission_required("members.read")
    def __call__(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        if per_page not in (5, 10, 20, 50, 100):
            per_page = 10
        search = request.args.get("search", "", type=str).strip()
        membership_filter = request.args.get("membership", "all", type=str)
        if membership_filter not in ("all", "with", "without"):
            membership_filter = "all"
        pagination = self.service.get_all_users_paginated(page=page, per_page=per_page, search=search, membership_filter=membership_filter)
        return render_template(
            "admin/members.html",
            members=pagination.items,
            pagination=pagination,
            per_page=per_page,
            search=search,
            membership_filter=membership_filter,
        )
