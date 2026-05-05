from flask import abort, render_template
from sqlalchemy import Sequence, cast

from app.forms import EditMemberForm
from app.repositories import RBACRepository
from app.services import UserService
from app.utils import permission_required


class EditMemberController:
    def __init__(self):
        super().__init__()
        self.service = UserService
        self.rbac_repository = RBACRepository

    @permission_required("members.update")
    def __call__(self, user_id):
        member = self.service.get_user_by_id(user_id)
        if not member:
            abort(404)

        form = EditMemberForm(obj=member)

        if member.membership:
            form.membership_start_date.data = member.membership.start_date
            form.membership_expiry_date.data = member.membership.expiry_date
            form.membership_initial_credits.data = member.membership.initial_credits
            form.membership_purchased_credits.data = member.membership.purchased_credits

        form.roles.choices = [(r.id, r.name) for r in self.rbac_repository.list_roles()]
        form.roles.data = [r.id for r in member.roles]
        return render_template("admin/edit_member.html", member=member, form=form)
