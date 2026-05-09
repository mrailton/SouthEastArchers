from flask import abort, current_app, flash, redirect, request, url_for
from flask_login import current_user

from app.models import Credit
from app.repositories import CreditRepository
from app.services import UserService
from app.utils import permission_required


class AdjustCreditsController:
    @permission_required("members.manage_membership")
    def __call__(self, user_id):
        member = UserService.get_user_by_id(user_id)
        if not member:
            abort(404)

        if not member.membership:
            flash("Member does not have a membership.", "error")
            return redirect(url_for("admin.member_detail", user_id=user_id))

        try:
            quantity = int(request.form.get("quantity", 0))
            action = request.form.get("action", "add")
            if quantity < 1:
                flash("Please enter a valid number of credits (minimum 1).", "error")
                return redirect(url_for("admin.member_detail", user_id=user_id))
        except ValueError:
            flash("Please enter a valid number of credits.", "error")
            return redirect(url_for("admin.member_detail", user_id=user_id))

        reason = request.form.get("reason", "").strip() or "Admin adjustment"

        if action == "remove":
            member.membership.remove_credits(quantity)
            signed_amount = -quantity
            verb = "Removed"
            preposition = "from"
        else:
            member.membership.add_credits(quantity)
            signed_amount = quantity
            verb = "Added"
            preposition = "to"

        credit = Credit(
            user_id=member.id,
            amount=signed_amount,
            payment_id=None,
            reason=reason,
            adjusted_by_id=current_user.id,
        )
        CreditRepository.add(credit)
        CreditRepository.save()

        current_app.logger.info(f"Admin {verb.lower()} {quantity} credits {preposition} user {member.id} ({member.email}). Reason: {reason}")

        flash(f"{verb} {quantity} credit(s) {preposition} {member.name}'s account.", "success")
        return redirect(url_for("admin.member_detail", user_id=user_id))
