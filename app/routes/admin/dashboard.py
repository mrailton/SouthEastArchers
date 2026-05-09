from app.controllers.admin.dashboard import DashboardController

from . import bp

bp.add_url_rule("/dashboard", view_func=DashboardController(), endpoint="dashboard", methods=["GET"])
