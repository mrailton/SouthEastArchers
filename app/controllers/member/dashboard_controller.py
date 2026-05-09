from flask import render_template, request
from flask_login import current_user, login_required

from app.repositories import PaymentRepository


class DashboardController:
    def __init__(self):
        super().__init__()
        self.payment_repository = PaymentRepository

    @login_required
    def __call__(self):
        user = current_user
        membership = user.membership
        shoots_attended = len(user.shoots)
        page = request.args.get("page", 1, type=int)
        payments = self.payment_repository.get_by_user_paginated(user.id, page=page, per_page=5)

        return render_template(
            "member/dashboard.html",
            user=user,
            membership=membership,
            shoots_attended=shoots_attended,
            payments=payments,
        )
