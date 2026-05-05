from app.controllers.admin.payments import (
    ApprovePaymentController,
    PendingPaymentsController,
    RejectPaymentController,
)

from . import bp

bp.add_url_rule("/payments", view_func=PendingPaymentsController(), endpoint="pending_payments", methods=["GET"])
bp.add_url_rule("/payments/<int:payment_id>/approve", view_func=ApprovePaymentController(), endpoint="approve_payment", methods=["POST"])
bp.add_url_rule("/payments/<int:payment_id>/reject", view_func=RejectPaymentController(), endpoint="reject_payment", methods=["POST"])
