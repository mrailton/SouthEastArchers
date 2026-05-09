from flask import Blueprint

from app.controllers.auth import (
    ForgotPasswordController,
    ForgotPasswordPostController,
    LoginController,
    LoginPostController,
    LogoutController,
    ResetPasswordController,
    ResetPasswordPostController,
    SignupController,
    SignupPostController,
)

bp = Blueprint("auth", __name__, url_prefix="/auth")

bp.add_url_rule("/login", view_func=LoginController(), endpoint="login", methods=["GET"])
bp.add_url_rule("/login", view_func=LoginPostController(), endpoint="login_post", methods=["POST"])
bp.add_url_rule("/signup", view_func=SignupController(), endpoint="signup", methods=["GET"])
bp.add_url_rule("/signup", view_func=SignupPostController(), endpoint="signup_post", methods=["POST"])
bp.add_url_rule("/logout", view_func=LogoutController(), endpoint="logout", methods=["GET"])
bp.add_url_rule("/forgot-password", view_func=ForgotPasswordController(), endpoint="forgot_password", methods=["GET"])
bp.add_url_rule("/forgot-password", view_func=ForgotPasswordPostController(), endpoint="forgot_password_post", methods=["POST"])
bp.add_url_rule("/reset-password/<token>", view_func=ResetPasswordController(), endpoint="reset_password", methods=["GET"])
bp.add_url_rule("/reset-password/<token>", view_func=ResetPasswordPostController(), endpoint="reset_password_post", methods=["POST"])
