from flask import Blueprint

from app.controllers.member import (
    ChangePasswordController,
    ChangePasswordPostController,
    CreditsController,
    DashboardController,
    ProfileController,
    ProfilePostController,
    ShootsController,
)

bp = Blueprint("member", __name__, url_prefix="/member")

bp.add_url_rule("/dashboard", view_func=DashboardController(), endpoint="dashboard", methods=["GET"])
bp.add_url_rule("/shoots", view_func=ShootsController(), endpoint="shoots", methods=["GET"])
bp.add_url_rule("/credits", view_func=CreditsController(), endpoint="credits", methods=["GET"])
bp.add_url_rule("/profile", view_func=ProfileController(), endpoint="profile", methods=["GET"])
bp.add_url_rule("/profile", view_func=ProfilePostController(), endpoint="profile_post", methods=["POST"])
bp.add_url_rule("/change-password", view_func=ChangePasswordController(), endpoint="change_password", methods=["GET"])
bp.add_url_rule("/change-password", view_func=ChangePasswordPostController(), endpoint="change_password_post", methods=["POST"])
