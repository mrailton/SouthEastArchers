from app.controllers.admin.shoots import (
    CreateShootController,
    CreateShootPostController,
    EditShootController,
    EditShootPostController,
    ShootsController,
)

from . import bp

bp.add_url_rule("/shoots", view_func=ShootsController(), endpoint="shoots", methods=["GET"])
bp.add_url_rule("/shoots/create", view_func=CreateShootController(), endpoint="create_shoot", methods=["GET"])
bp.add_url_rule("/shoots/create", view_func=CreateShootPostController(), endpoint="create_shoot_post", methods=["POST"])
bp.add_url_rule("/shoots/<int:shoot_id>/edit", view_func=EditShootController(), endpoint="edit_shoot", methods=["GET"])
bp.add_url_rule("/shoots/<int:shoot_id>/edit", view_func=EditShootPostController(), endpoint="edit_shoot_post", methods=["POST"])
