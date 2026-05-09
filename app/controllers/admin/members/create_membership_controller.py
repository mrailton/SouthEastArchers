from flask import abort, flash, redirect, url_for

from app.services import MembershipService, UserService
from app.utils import permission_required


class CreateMembershipController:
    @permission_required("members.manage_membership")
    def __call__(self, user_id):
        member = UserService.get_user_by_id(user_id)
        if not member:
            abort(404)

        result = MembershipService.create_membership(member)
        flash(result.message, "success" if result.success else "error")
        return redirect(url_for("admin.member_detail", user_id=user_id))
