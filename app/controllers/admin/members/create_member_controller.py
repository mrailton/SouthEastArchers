from flask import render_template

from app.forms import CreateMemberForm
from app.repositories import RBACRepository
from app.utils import permission_required


class CreateMemberController:
    def __init__(self):
        super().__init__()
        self.rbac_repository = RBACRepository

    @permission_required("members.create")
    def __call__(self):
        form = CreateMemberForm()
        form.roles.choices = [(r.id, r.name) for r in self.rbac_repository.list_roles()]
        return render_template("admin/create_member.html", form=form)
