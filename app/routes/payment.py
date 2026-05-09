from flask import Blueprint

from app.controllers.payment import (
    CompleteCheckoutController,
    CreditsCashPaymentController,
    CreditsPaymentController,
    CreditsPaymentPostController,
    HistoryController,
    MembershipCashPaymentController,
    MembershipPaymentController,
    MembershipPaymentPostController,
    ShowCheckoutController,
)

bp = Blueprint("payment", __name__, url_prefix="/payment")

bp.add_url_rule("/checkout/<checkout_id>", view_func=ShowCheckoutController(), endpoint="show_checkout", methods=["GET"])
bp.add_url_rule("/checkout/<checkout_id>/complete", view_func=CompleteCheckoutController(), endpoint="complete_checkout", methods=["POST"])
bp.add_url_rule("/membership", view_func=MembershipPaymentController(), endpoint="membership_payment", methods=["GET"])
bp.add_url_rule("/membership", view_func=MembershipPaymentPostController(), endpoint="membership_payment_post", methods=["POST"])
bp.add_url_rule("/credits", view_func=CreditsPaymentController(), endpoint="credits", methods=["GET"])
bp.add_url_rule("/credits", view_func=CreditsPaymentPostController(), endpoint="credits_post", methods=["POST"])
bp.add_url_rule("/history", view_func=HistoryController(), endpoint="history", methods=["GET"])
bp.add_url_rule("/membership/cash", view_func=MembershipCashPaymentController(), endpoint="membership_cash_payment", methods=["POST"])
bp.add_url_rule("/credits/cash", view_func=CreditsCashPaymentController(), endpoint="credits_cash_payment", methods=["POST"])
