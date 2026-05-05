from flask import render_template
from flask_login import current_user, login_required

from app.repositories import CreditRepository


class CreditsController:
    def __init__(self):
        super().__init__()
        self.credit_repository = CreditRepository

    @login_required
    def __call__(self):
        user = current_user
        credits = self.credit_repository.get_by_user(user.id)
        return render_template("member/credits.html", credits=credits, user=user)
