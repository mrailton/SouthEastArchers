from flask import flash, render_template

from app.forms import CreateMemberForm
from app.repositories import RBACRepository
from app.services import UserService
from app.utils import permission_required


class CreateMemberPostController:
    def __init__(self):
        super().__init__()
        self.service = UserService
        self.rbac_repository = RBACRepository

    @permission_required("members.create")
    def __call__(self):
        form = CreateMemberForm()
        form.roles.choices = [(r.id, r.name) for r in self.rbac_repository.list_roles()]

        if form.validate_on_submit():
            result = self.service.create_member(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                password=form.password.data or "changeme123",
                role_ids=form.roles.data,
                create_membership=form.create_membership.data,
                qualification=form.qualification.data if hasattr(form, "qualification") else "none",
            )

            if not result.success:
                flash(result.message, "error")
                return render_template("admin/create_member.html", form=form)

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("admin/create_member.html", form=form)
