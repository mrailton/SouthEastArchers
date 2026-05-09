from app.controllers.admin.members import (
    ActivateMembershipController,
    ActivateUserController,
    AdjustCreditsController,
    CreateMemberController,
    CreateMemberPostController,
    CreateMembershipController,
    EditMemberController,
    EditMemberPostController,
    MemberDetailController,
    MembersController,
    RenewMembershipController,
)

from . import bp

bp.add_url_rule("/members", view_func=MembersController(), endpoint="members", methods=["GET"])
bp.add_url_rule("/members/<int:user_id>", view_func=MemberDetailController(), endpoint="member_detail", methods=["GET"])
bp.add_url_rule("/members/<int:user_id>/membership/renew", view_func=RenewMembershipController(), endpoint="renew_membership", methods=["POST"])
bp.add_url_rule("/members/<int:user_id>/membership/create", view_func=CreateMembershipController(), endpoint="create_membership", methods=["POST"])
bp.add_url_rule("/members/<int:user_id>/membership/activate", view_func=ActivateMembershipController(), endpoint="activate_membership", methods=["POST"])
bp.add_url_rule("/members/<int:user_id>/activate", view_func=ActivateUserController(), endpoint="activate_user", methods=["POST"])
bp.add_url_rule("/members/create", view_func=CreateMemberController(), endpoint="create_member", methods=["GET"])
bp.add_url_rule("/members/create", view_func=CreateMemberPostController(), endpoint="create_member_post", methods=["POST"])
bp.add_url_rule("/members/<int:user_id>/edit", view_func=EditMemberController(), endpoint="edit_member", methods=["GET"])
bp.add_url_rule("/members/<int:user_id>/edit", view_func=EditMemberPostController(), endpoint="edit_member_post", methods=["POST"])
bp.add_url_rule("/members/<int:user_id>/credits/adjust", view_func=AdjustCreditsController(), endpoint="adjust_credits", methods=["POST"])
