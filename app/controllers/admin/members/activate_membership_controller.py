from flask import abort, flash, redirect, url_for

from app.enums import PaymentType
from app.events import membership_activated
from app.repositories import PaymentRepository
from app.services import MembershipService, UserService
from app.utils import permission_required


class ActivateMembershipController:
    @permission_required("members.manage_membership")
    def __call__(self, user_id):
        member = UserService.get_user_by_id(user_id)
        if not member:
            abort(404)

        result = MembershipService.activate_membership(member)

        if not result.success:
            flash(result.message, "error")
            return redirect(url_for("admin.member_detail", user_id=user_id))

        payment = PaymentRepository.get_completed_for_user(user_id, PaymentType.MEMBERSHIP)

        if payment:
            membership_activated.send(user_id=member.id, payment_id=payment.id)
            flash(f"Membership activated for {member.name}! Receipt email sent.", "success")
        else:
            flash(f"Membership activated for {member.name}!", "success")

        return redirect(url_for("admin.member_detail", user_id=user_id))
