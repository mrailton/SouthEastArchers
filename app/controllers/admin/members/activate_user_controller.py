from flask import abort, flash, redirect, url_for

from app.events import user_activated
from app.repositories import UserRepository
from app.services import UserService
from app.utils import permission_required


class ActivateUserController:
    @permission_required("members.activate_account")
    def __call__(self, user_id):
        member = UserService.get_user_by_id(user_id)
        if not member:
            abort(404)

        if member.is_active:
            flash(f"{member.name}'s account is already active.", "warning")
            return redirect(url_for("admin.member_detail", user_id=user_id))

        member.is_active = True
        UserRepository.save()

        user_activated.send(user_id=user_id)
        flash(f"Account activated for {member.name}! Welcome email sent.", "success")

        return redirect(url_for("admin.member_detail", user_id=user_id))
