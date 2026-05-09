from flask import render_template

from app.repositories import PaymentRepository, UserRepository
from app.utils import permission_required


class PendingPaymentsController:
    def __init__(self):
        super().__init__()
        self.payment_repository = PaymentRepository
        self.user_repository = UserRepository

    @permission_required("payments.approve")
    def __call__(self):
        payments = self.payment_repository.get_pending_cash()

        payment_data = []
        for payment in payments:
            user = self.user_repository.get_by_id(payment.user_id)
            payment_data.append({"payment": payment, "user": user})

        return render_template("admin/pending_payments.html", payment_data=payment_data)
