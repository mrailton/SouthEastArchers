from flask import Blueprint

bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import dashboard, events, members, news, roles, settings, shoots  # noqa: E402
