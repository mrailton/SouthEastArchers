from flask import Blueprint

bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import dashboard, events, finance, members, news, payments, roles, settings, shoots  # noqa: E402
