from flask import render_template
from flask_login import current_user, login_required

from app.repositories import PaymentRepository


class HistoryController:
    def __init__(self):
        super().__init__()
        self.payment_repository = PaymentRepository

    @login_required
    def __call__(self):
        user = current_user
        payments = self.payment_repository.get_by_user(user.id)
        return render_template("payment/history.html", payments=payments)
