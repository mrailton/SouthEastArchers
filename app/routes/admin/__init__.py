from flask import Blueprint

from app.utils.decorators import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import dashboard, events, members, news, settings, shoots  # noqa: E402
