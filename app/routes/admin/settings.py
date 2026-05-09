from app.controllers.admin.settings import SettingsController, SettingsPostController

from . import bp

bp.add_url_rule("/settings", view_func=SettingsController(), endpoint="settings", methods=["GET"])
bp.add_url_rule("/settings", view_func=SettingsPostController(), endpoint="settings_post", methods=["POST"])
