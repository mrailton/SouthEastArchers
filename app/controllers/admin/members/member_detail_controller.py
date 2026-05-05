from flask import abort, render_template

from app.services import UserService
from app.utils import permission_required


class MemberDetailController:
    def __init__(self):
        super().__init__()
        self.service = UserService

    @permission_required("members.read")
    def __call__(self, user_id):
        member = self.service.get_user_by_id(user_id)
        if not member:
            abort(404)
        return render_template("admin/member_detail.html", member=member)
