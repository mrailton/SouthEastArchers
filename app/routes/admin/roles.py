from app.controllers.admin.roles import (
    CreateRoleController,
    CreateRolePostController,
    DeleteRoleController,
    EditRoleController,
    EditRolePostController,
    RolesIndexController,
)

from . import bp

bp.add_url_rule("/roles", view_func=RolesIndexController(), endpoint="roles_index", methods=["GET"])
bp.add_url_rule("/roles/create", view_func=CreateRoleController(), endpoint="create_role", methods=["GET"])
bp.add_url_rule("/roles/create", view_func=CreateRolePostController(), endpoint="create_role_post", methods=["POST"])
bp.add_url_rule("/roles/<int:role_id>/edit", view_func=EditRoleController(), endpoint="edit_role", methods=["GET"])
bp.add_url_rule("/roles/<int:role_id>/edit", view_func=EditRolePostController(), endpoint="edit_role_post", methods=["POST"])
bp.add_url_rule("/roles/<int:role_id>/delete", view_func=DeleteRoleController(), endpoint="delete_role", methods=["POST"])
