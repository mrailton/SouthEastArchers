from flask import abort, flash, redirect, render_template, url_for

from app.forms import EditMemberForm
from app.repositories import RBACRepository
from app.services import UserService
from app.utils import permission_required


class EditMemberPostController:
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
        form.roles.choices = [(r.id, r.name) for r in self.rbac_repository.list_roles()]

        if form.validate_on_submit():
            result = self.service.update_member(
                user=member,
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                qualification=form.qualification.data,
                qualification_detail=form.qualification_detail.data or None,
                role_ids=form.roles.data,
                is_active=form.is_active.data,
                password=form.password.data or None,
                membership_start_date=form.membership_start_date.data,
                membership_expiry_date=form.membership_expiry_date.data,
                membership_initial_credits=form.membership_initial_credits.data,
                membership_purchased_credits=form.membership_purchased_credits.data,
            )

            flash(result.message, "success" if result.success else "error")
            if result.success:
                return redirect(url_for("admin.member_detail", user_id=user_id))

        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "error")

        return render_template("admin/edit_member.html", member=member, form=form)
